// app/chat.tsx - Part of the PrepSense mobile app
import { View, Text, SafeAreaView, StyleSheet, TextInput, TouchableOpacity, KeyboardAvoidingView, Platform, ScrollView, StatusBar, ActivityIndicator, Alert, Image, Modal } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useState, useEffect } from 'react';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { CustomHeader } from '../components/CustomHeader';
import { sendChatMessage, generateRecipeImage } from '../../services/api';
import { Recipe } from '../../services/recipeService';
import Markdown from 'react-native-markdown-display';
import { useTabData } from '../../context/TabDataProvider';
import RecipeDetailCardV3 from '../../components/recipes/RecipeDetailCardV3';

type Message = {
  id: string;
  text: string;
  sender: 'user' | 'ai';
  recipes?: Recipe[];
};

const defaultSuggestedMessages = [
  "What can I make for dinner?",
  "What can I make with only ingredients I have?",
  "What's good for breakfast?",
  "Show me healthy recipes",
  "Quick meals under 20 minutes",
  "What should I cook tonight?",
];

// Enhanced Recipe Detail Modal with Spoonacular-style design
function RecipeDetailModal({ recipe, visible, onClose }: { 
  recipe: Recipe | null; 
  visible: boolean; 
  onClose: () => void;
}) {
  if (!recipe) return null;

  // Normalize the recipe data to ensure consistency with Spoonacular format
  const normalizedRecipe = {
    ...recipe,
    // Ensure all required Spoonacular fields are present
    title: recipe.title || recipe.name || 'Untitled Recipe',
    readyInMinutes: recipe.readyInMinutes || recipe.time || 30,
    servings: recipe.servings || 4,
    image: recipe.image || `https://via.placeholder.com/556x370.png/40E0D0/000000?text=${(recipe.title || recipe.name || 'Recipe').slice(0, 20)}`,
    
    // Ensure nutrition data is structured properly
    nutrition: recipe.nutrition || {
      calories: 0,
      protein: 0,
      carbs: 0,
      fat: 0,
      nutrients: []
    },
    
    // Ensure ingredients are in extendedIngredients format if available
    extendedIngredients: recipe.extendedIngredients || (recipe.ingredients ? 
      recipe.ingredients.map((ing, index) => ({
        id: index + 1,
        name: typeof ing === 'string' ? ing : ing.name || ing.ingredient_name || '',
        original: typeof ing === 'string' ? ing : ing.original || ing.name || ing.ingredient_name || '',
        amount: typeof ing === 'object' ? ing.amount || ing.quantity : undefined,
        unit: typeof ing === 'object' ? ing.unit : ''
      })) : []
    ),
    
    // Ensure instructions are properly structured
    analyzedInstructions: recipe.analyzedInstructions || (recipe.instructions ? [{
      name: '',
      steps: Array.isArray(recipe.instructions) ? 
        recipe.instructions.map((inst, index) => ({
          number: index + 1,
          step: typeof inst === 'string' ? inst : inst.step || String(inst),
          ingredients: [],
          equipment: []
        })) : []
    }] : []),
    
    // Add default metadata
    cuisines: recipe.cuisines || [],
    diets: recipe.diets || [],
    dishTypes: recipe.dishTypes || ['main course'],
    pricePerServing: recipe.pricePerServing || 0,
    sourceUrl: recipe.sourceUrl || `https://prepsense.ai/chat-recipe/${recipe.id || 'unknown'}`
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={onClose}
    >
      <RecipeDetailCardV3
        recipe={normalizedRecipe}
        onBack={onClose}
        onRatingSubmitted={(rating) => {
          console.log('Recipe rated:', rating);
          // TODO: Implement rating API call for chat recipes
        }}
      />
    </Modal>
  );
}

// Enhanced Recipe Card Component with Spoonacular-style design
function RecipeCard({ recipe, onPress }: { recipe: Recipe; onPress: () => void }) {
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [imageLoading, setImageLoading] = useState(true);

  useEffect(() => {
    // Check if recipe has image first, otherwise fetch one
    if (recipe.image) {
      setImageUrl(recipe.image);
      setImageLoading(false);
    } else {
      // Fetch image for the recipe
      const fetchImage = async () => {
        try {
          const response = await generateRecipeImage(
            recipe.name || recipe.title || 'Recipe',
            "professional food photography",
            false // Use Unsplash for speed
          );
          setImageUrl(response.image_url);
        } catch (error) {
          console.error('Error fetching recipe image:', error);
        } finally {
          setImageLoading(false);
        }
      };

      fetchImage();
    }
  }, [recipe.name, recipe.title, recipe.image]);

  // Normalize recipe data for display using enriched Spoonacular-style data
  const recipeName = recipe.name || recipe.title || 'Untitled Recipe';
  const recipeTime = recipe.time || recipe.readyInMinutes || 30;
  const servings = recipe.servings || 4;
  const calories = recipe.nutrition?.calories || 0;
  const pricePerServing = recipe.pricePerServing || 0;
  
  // Calculate match score from ingredients
  const totalIngredients = (recipe.extendedIngredients?.length || 
    recipe.ingredients?.length || 
    (recipe.available_ingredients?.length || 0) + (recipe.missing_ingredients?.length || 0)) || 10;
  const availableCount = recipe.available_ingredients?.length || 0;
  const matchScore = totalIngredients > 0 ? Math.round((availableCount / totalIngredients) * 100) : 85;

  // Extract cuisines and diets for tags
  const cuisines = recipe.cuisines || [];
  const diets = recipe.diets || [];
  const allTags = [...cuisines, ...diets].slice(0, 2); // Show max 2 tags

  return (
    <TouchableOpacity style={styles.enhancedRecipeCard} onPress={onPress}>
      {/* Recipe Image with Overlay */}
      <View style={styles.enhancedImageContainer}>
        {imageLoading ? (
          <View style={styles.enhancedImagePlaceholder}>
            <ActivityIndicator size="small" color="#297A56" />
          </View>
        ) : imageUrl ? (
          <>
            <Image source={{ uri: imageUrl }} style={styles.enhancedRecipeImage} />
            <View style={styles.imageOverlay} />
          </>
        ) : (
          <View style={styles.enhancedImagePlaceholder}>
            <Ionicons name="image-outline" size={32} color="#ccc" />
          </View>
        )}
        
        {/* Match Score Badge */}
        <View style={[styles.matchBadge, { backgroundColor: matchScore >= 80 ? '#4CAF50' : matchScore >= 60 ? '#FF9800' : '#F44336' }]}>
          <Text style={styles.matchBadgeText}>{matchScore}%</Text>
        </View>

        {/* Bookmark Icon */}
        <TouchableOpacity style={styles.bookmarkButton}>
          <Ionicons name="bookmark-outline" size={18} color="#fff" />
        </TouchableOpacity>
      </View>

      {/* Recipe Content */}
      <View style={styles.enhancedRecipeContent}>
        <View style={styles.titleRow}>
          <Text style={styles.enhancedRecipeTitle} numberOfLines={2}>{recipeName}</Text>
        </View>
        
        {/* Tags */}
        {allTags.length > 0 && (
          <View style={styles.tagsRow}>
            {allTags.map((tag, index) => (
              <View key={index} style={styles.tag}>
                <Text style={styles.tagText}>{tag}</Text>
              </View>
            ))}
          </View>
        )}
        
        {/* Metrics Row */}
        <View style={styles.enhancedMetricsRow}>
          <View style={styles.metricItem}>
            <Ionicons name="time-outline" size={14} color="#666" />
            <Text style={styles.metricText}>{recipeTime} min</Text>
          </View>
          <View style={styles.metricItem}>
            <Ionicons name="people-outline" size={14} color="#666" />
            <Text style={styles.metricText}>{servings}</Text>
          </View>
          {calories > 0 && (
            <View style={styles.metricItem}>
              <Text style={styles.metricText}>{calories} kcal</Text>
            </View>
          )}
          {pricePerServing > 0 && (
            <View style={styles.metricItem}>
              <Text style={styles.metricText}>${(pricePerServing / 100).toFixed(2)}</Text>
            </View>
          )}
        </View>
        
        {/* Ingredients Status */}
        {(recipe.available_ingredients?.length > 0 || recipe.missing_ingredients?.length > 0) && (
          <View style={styles.ingredientsStatus}>
            <View style={styles.statusRow}>
              {availableCount > 0 && (
                <View style={styles.statusItem}>
                  <Ionicons name="checkmark-circle" size={14} color="#4CAF50" />
                  <Text style={styles.availableText}>{availableCount} available</Text>
                </View>
              )}
              {recipe.missing_ingredients?.length > 0 && (
                <View style={styles.statusItem}>
                  <Ionicons name="close-circle" size={14} color="#F44336" />
                  <Text style={styles.missingText}>{recipe.missing_ingredients.length} missing</Text>
                </View>
              )}
            </View>
          </View>
        )}
      </View>
    </TouchableOpacity>
  );
}

export default function ChatScreen() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const [showPreferenceChoice, setShowPreferenceChoice] = useState(false);
  const [userPreferences, setUserPreferences] = useState<any>(null);
  const [usePreferences, setUsePreferences] = useState(true);
  const [selectedRecipe, setSelectedRecipe] = useState<Recipe | null>(null);
  const [showRecipeDetail, setShowRecipeDetail] = useState(false);
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const params = useLocalSearchParams();
  const { chatData } = useTabData();
  
  // Use preloaded suggestions if available, otherwise use defaults
  const suggestedMessages = chatData?.suggestedQuestions || defaultSuggestedMessages;
  
  // Check for suggestion from navigation
  useEffect(() => {
    if (params.suggestion) {
      sendMessage(params.suggestion as string);
    }
  }, [params.suggestion]);

  const sendMessage = async (messageText: string, withPreferences: boolean = usePreferences) => {
    if (isLoading) return;
    
    setIsLoading(true);
    setShowSuggestions(false);
    
    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      text: messageText,
      sender: 'user',
    };
    
    setMessages(prev => [...prev, userMessage]);
    
    try {
      // Call the actual API
      const response = await sendChatMessage(messageText, 111, withPreferences);
      
      // Check if we should show preference choice
      if (response.show_preference_choice && response.user_preferences && messages.length === 1) {
        setUserPreferences(response.user_preferences);
        setShowPreferenceChoice(true);
      }
      
      // Add AI response
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: response.response,
        sender: 'ai',
        recipes: response.recipes,
      };
      
      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      
      // Add error message
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: "Sorry, I'm having trouble connecting to the server. Please make sure the backend is running and try again.",
        sender: 'ai',
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSend = async () => {
    if (inputText.trim() === '') return;
    
    const messageText = inputText.trim();
    setInputText('');
    await sendMessage(messageText);
  };

  const handleSuggestedMessage = async (suggestion: string) => {
    await sendMessage(suggestion);
  };

  return (
    <>
      <View style={styles.container}>
        <StatusBar barStyle="dark-content" />
        <View style={[styles.content, { paddingBottom: insets.bottom }]}>
        <ScrollView 
          style={styles.messagesContainer}
          contentContainerStyle={styles.messagesContent}
          contentInset={{ top: 60 }} // Add padding to account for the header
        >
          {messages.length === 0 ? (
            <View style={styles.emptyState}>
              <Ionicons name="chatbubble-ellipses" size={48} color="#ccc" />
              <Text style={styles.emptyStateText}>Ask me anything about your pantry!</Text>
              
              {showSuggestions && (
                <View style={styles.suggestionsContainer}>
                  <Text style={styles.suggestionsTitle}>Try asking:</Text>
                  <View style={styles.suggestionBubbles}>
                    {suggestedMessages.map((suggestion, index) => (
                      <TouchableOpacity
                        key={index}
                        style={styles.suggestionBubble}
                        onPress={() => handleSuggestedMessage(suggestion)}
                        disabled={isLoading}
                      >
                        <Text style={styles.suggestionText}>{suggestion}</Text>
                      </TouchableOpacity>
                    ))}
                  </View>
                </View>
              )}
            </View>
          ) : (
            messages.map((message) => (
              <View key={message.id}>
                <View 
                  style={[
                    styles.messageBubble,
                    message.sender === 'user' ? styles.userBubble : styles.aiBubble,
                  ]}
                >
                  {message.sender === 'user' ? (
                    <Text style={styles.userText}>
                      {message.text}
                    </Text>
                  ) : (
                    <Markdown 
                      style={markdownStyles}
                    >
                      {message.text}
                    </Markdown>
                  )}
                </View>
                
                {/* Show preference choice after first AI response */}
                {showPreferenceChoice && message.sender === 'ai' && messages.indexOf(message) === 1 && (
                  <View style={styles.preferenceCard}>
                    <Text style={styles.preferenceTitle}>Your Saved Preferences:</Text>
                    {userPreferences && (
                      <>
                        {userPreferences.dietary_preference && userPreferences.dietary_preference.length > 0 && (
                          <Text style={styles.preferenceItem}>
                            🥗 Dietary: {userPreferences.dietary_preference.join(', ')}
                          </Text>
                        )}
                        {userPreferences.allergens && userPreferences.allergens.length > 0 && (
                          <Text style={styles.preferenceItem}>
                            ⚠️ Allergens: {userPreferences.allergens.join(', ')}
                          </Text>
                        )}
                        {userPreferences.cuisine_preference && userPreferences.cuisine_preference.length > 0 && (
                          <Text style={styles.preferenceItem}>
                            🌍 Cuisines: {userPreferences.cuisine_preference.join(', ')}
                          </Text>
                        )}
                      </>
                    )}
                    <Text style={styles.preferenceQuestion}>
                      Would you like me to use these preferences for recipe recommendations?
                    </Text>
                    <View style={styles.preferenceButtons}>
                      <TouchableOpacity
                        style={[styles.preferenceButton, styles.yesButton]}
                        onPress={() => {
                          setShowPreferenceChoice(false);
                          setUsePreferences(true);
                        }}
                      >
                        <Text style={styles.preferenceButtonText}>Yes, use my preferences</Text>
                      </TouchableOpacity>
                      <TouchableOpacity
                        style={[styles.preferenceButton, styles.noButton]}
                        onPress={() => {
                          setShowPreferenceChoice(false);
                          setUsePreferences(false);
                          // Resend the last message without preferences
                          const lastUserMessage = messages.find(m => m.sender === 'user');
                          if (lastUserMessage) {
                            sendMessage(lastUserMessage.text, false);
                          }
                        }}
                      >
                        <Text style={styles.preferenceButtonText}>No, show all recipes</Text>
                      </TouchableOpacity>
                    </View>
                  </View>
                )}
                
                {/* Show recipe cards for AI messages with recipes */}
                {message.sender === 'ai' && message.recipes && message.recipes.length > 0 && (
                  <View style={styles.recipesContainer}>
                    {message.recipes.map((recipe, index) => (
                      <RecipeCard
                        key={index}
                        recipe={recipe}
                        onPress={() => {
                          setSelectedRecipe(recipe);
                          setShowRecipeDetail(true);
                        }}
                      />
                    ))}
                  </View>
                )}
              </View>
            ))
          )}
          
          {/* Show suggestions even after messages if user wants them */}
          {messages.length > 0 && showSuggestions && (
            <View style={styles.inlineSuggestionsContainer}>
              <Text style={styles.inlineSuggestionsTitle}>Quick suggestions:</Text>
              <ScrollView 
                horizontal 
                showsHorizontalScrollIndicator={false}
                contentContainerStyle={styles.inlineSuggestionBubbles}
              >
                {suggestedMessages.slice(0, 3).map((suggestion, index) => (
                  <TouchableOpacity
                    key={index}
                    style={styles.inlineSuggestionBubble}
                    onPress={() => handleSuggestedMessage(suggestion)}
                    disabled={isLoading}
                  >
                    <Text style={styles.inlineSuggestionText}>{suggestion}</Text>
                  </TouchableOpacity>
                ))}
              </ScrollView>
            </View>
          )}
        </ScrollView>
        
        <KeyboardAvoidingView 
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.inputContainer}
        >
          <TextInput
            style={styles.input}
            value={inputText}
            onChangeText={setInputText}
            placeholder="Type a message..."
            placeholderTextColor="#999"
          />
          {messages.length > 0 && (
            <TouchableOpacity 
              style={styles.suggestionsToggle} 
              onPress={() => setShowSuggestions(!showSuggestions)}
            >
              <Ionicons 
                name={showSuggestions ? "bulb" : "bulb-outline"} 
                size={20} 
                color="#297A56" 
              />
            </TouchableOpacity>
          )}
          <TouchableOpacity 
            style={styles.sendButton} 
            onPress={handleSend}
            disabled={inputText.trim() === '' || isLoading}
          >
            {isLoading ? (
              <ActivityIndicator size="small" color="#297A56" />
            ) : (
              <Ionicons 
                name="send" 
                size={24} 
                color={inputText.trim() === '' ? '#ccc' : '#297A56'} 
              />
            )}
          </TouchableOpacity>
        </KeyboardAvoidingView>
      </View>
      </View>

      {/* Recipe Detail Modal */}
      <RecipeDetailModal
        recipe={selectedRecipe}
        visible={showRecipeDetail}
        onClose={() => {
          setShowRecipeDetail(false);
          setSelectedRecipe(null);
        }}
      />
    </>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  content: {
    flex: 1,
  },
  header: {
    // Header styles are now in CustomHeader component
  },
  messagesContainer: {
    flex: 1,
    padding: 16,
  },
  messagesContent: {
    paddingBottom: 16,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 100,
  },
  emptyStateText: {
    marginTop: 16,
    color: '#999',
    fontSize: 16,
  },
  messageBubble: {
    maxWidth: '80%',
    padding: 12,
    borderRadius: 16,
    marginBottom: 8,
  },
  userBubble: {
    alignSelf: 'flex-end',
    backgroundColor: '#297A56',
    borderBottomRightRadius: 4,
  },
  aiBubble: {
    alignSelf: 'flex-start',
    backgroundColor: '#f0f0f0',
    borderBottomLeftRadius: 4,
  },
  userText: {
    color: '#fff',
  },
  aiText: {
    color: '#333',
  },
  inputContainer: {
    flexDirection: 'row',
    padding: 12,
    paddingBottom: 20, // Add extra padding to avoid + button overlap
    borderTopWidth: 1,
    borderTopColor: '#eee',
    backgroundColor: '#fff',
  },
  input: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 24,
    paddingHorizontal: 16,
    paddingVertical: 10,
    marginRight: 8,
    fontSize: 16,
  },
  sendButton: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#f0f0f0',
    justifyContent: 'center',
    alignItems: 'center',
  },
  recipesContainer: {
    marginTop: 8,
    marginLeft: 16,
  },
  recipeCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#e0e0e0',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 2,
    flexDirection: 'row',
    overflow: 'hidden',
  },
  recipeImageContainer: {
    width: 120,
    height: 120,
  },
  recipeImage: {
    width: '100%',
    height: '100%',
    resizeMode: 'cover',
  },
  imagePlaceholder: {
    width: '100%',
    height: '100%',
    backgroundColor: '#f5f5f5',
    justifyContent: 'center',
    alignItems: 'center',
  },
  recipeContent: {
    flex: 1,
    padding: 12,
  },
  recipeTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 6,
  },
  recipeMetrics: {
    flexDirection: 'row',
    justifyContent: 'flex-start',
    marginBottom: 8,
    flexWrap: 'wrap',
    gap: 8,
  },
  recipeTime: {
    fontSize: 12,
    color: '#666',
  },
  recipeMatch: {
    fontSize: 12,
    color: '#297A56',
    fontWeight: '600',
  },
  ingredientSection: {
    marginBottom: 6,
  },
  ingredientTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: '#333',
    marginBottom: 2,
  },
  availableIngredients: {
    fontSize: 12,
    color: '#297A56',
    lineHeight: 16,
  },
  missingIngredients: {
    fontSize: 12,
    color: '#DC2626',
    lineHeight: 16,
  },

  // Enhanced Recipe Card Styles (Spoonacular-style)
  enhancedRecipeCard: {
    backgroundColor: '#fff',
    borderRadius: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.12,
    shadowRadius: 8,
    elevation: 6,
    overflow: 'hidden',
  },
  enhancedImageContainer: {
    height: 180,
    position: 'relative',
  },
  enhancedRecipeImage: {
    width: '100%',
    height: '100%',
    resizeMode: 'cover',
  },
  enhancedImagePlaceholder: {
    width: '100%',
    height: '100%',
    backgroundColor: '#E8F5E8',
    justifyContent: 'center',
    alignItems: 'center',
  },
  imageOverlay: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    height: 60,
    backgroundColor: 'rgba(0,0,0,0.3)',
  },
  matchBadge: {
    position: 'absolute',
    top: 12,
    right: 12,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 2,
    elevation: 3,
  },
  matchBadgeText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '700',
  },
  bookmarkButton: {
    position: 'absolute',
    top: 12,
    left: 12,
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: 'rgba(0,0,0,0.3)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  enhancedRecipeContent: {
    padding: 16,
  },
  titleRow: {
    marginBottom: 8,
  },
  enhancedRecipeTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1A1A1A',
    lineHeight: 24,
  },
  tagsRow: {
    flexDirection: 'row',
    marginBottom: 12,
    gap: 6,
  },
  tag: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    backgroundColor: '#E8F5E8',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#297A56',
  },
  tagText: {
    fontSize: 11,
    color: '#297A56',
    fontWeight: '600',
    textTransform: 'capitalize',
  },
  enhancedMetricsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
    gap: 16,
  },
  metricItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  metricText: {
    fontSize: 13,
    color: '#666',
    fontWeight: '500',
  },
  ingredientsStatus: {
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#F0F0F0',
  },
  statusRow: {
    flexDirection: 'row',
    gap: 16,
  },
  statusItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  availableText: {
    fontSize: 12,
    color: '#4CAF50',
    fontWeight: '600',
  },
  missingText: {
    fontSize: 12,
    color: '#F44336',
    fontWeight: '600',
  },
  nutritionRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
  },
  nutritionText: {
    fontSize: 12,
    color: '#666',
  },
  suggestionsContainer: {
    marginTop: 24,
    width: '100%',
    paddingHorizontal: 20,
  },
  suggestionsTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 12,
    textAlign: 'center',
  },
  suggestionBubbles: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    gap: 8,
  },
  suggestionBubble: {
    backgroundColor: '#F0F7F4',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#297A56',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 1,
  },
  suggestionText: {
    fontSize: 14,
    color: '#297A56',
    fontWeight: '500',
    textAlign: 'center',
  },
  inlineSuggestionsContainer: {
    marginTop: 16,
    paddingHorizontal: 16,
    paddingBottom: 8,
  },
  inlineSuggestionsTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#666',
    marginBottom: 8,
  },
  inlineSuggestionBubbles: {
    paddingRight: 16,
  },
  inlineSuggestionBubble: {
    backgroundColor: '#F8F9FA',
    borderRadius: 16,
    paddingHorizontal: 12,
    paddingVertical: 8,
    marginRight: 8,
    borderWidth: 1,
    borderColor: '#E9ECEF',
  },
  inlineSuggestionText: {
    fontSize: 12,
    color: '#6C757D',
    fontWeight: '500',
  },
  suggestionsToggle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#f0f0f0',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 8,
  },
  tapHintContainer: {
    alignItems: 'center',
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
  },
  tapHint: {
    fontSize: 12,
    color: '#999',
    fontStyle: 'italic',
  },
  warningSection: {
    backgroundColor: '#FEF3C7',
    borderRadius: 8,
    padding: 8,
    marginTop: 8,
  },
  warningText: {
    fontSize: 12,
    color: '#92400E',
    fontWeight: '600',
  },
  preferencesSection: {
    backgroundColor: '#D1FAE5',
    borderRadius: 8,
    padding: 8,
    marginTop: 8,
  },
  preferencesText: {
    fontSize: 12,
    color: '#065F46',
    fontWeight: '600',
  },
  preferenceCard: {
    backgroundColor: '#F0F7F4',
    borderRadius: 12,
    padding: 16,
    marginHorizontal: 16,
    marginVertical: 8,
    borderWidth: 1,
    borderColor: '#297A56',
  },
  preferenceTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  preferenceItem: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  preferenceQuestion: {
    fontSize: 15,
    color: '#333',
    marginTop: 12,
    marginBottom: 16,
  },
  preferenceButtons: {
    flexDirection: 'row',
    gap: 12,
  },
  preferenceButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  yesButton: {
    backgroundColor: '#297A56',
  },
  noButton: {
    backgroundColor: '#666',
  },
  preferenceButtonText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 14,
  },
});

const markdownStyles = {
  body: {
    color: '#333',
    fontSize: 16,
    lineHeight: 22,
  },
  paragraph: {
    marginBottom: 8,
    fontSize: 16,
    lineHeight: 22,
    color: '#333',
  },
  heading1: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 8,
    color: '#333',
  },
  heading2: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 6,
    color: '#333',
  },
  heading3: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 4,
    color: '#333',
  },
  strong: {
    fontWeight: 'bold',
    color: '#333',
  },
  listItem: {
    marginBottom: 4,
    fontSize: 16,
    color: '#333',
  },
  listItemBullet: {
    color: '#297A56',
    marginRight: 4,
  },
  listItemNumber: {
    color: '#297A56',
    marginRight: 4,
  },
  bullet_list: {
    marginBottom: 8,
  },
  ordered_list: {
    marginBottom: 8,
  },
  link: {
    color: '#297A56',
    textDecorationLine: 'underline',
  },
};
