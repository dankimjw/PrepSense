// app/chat.tsx - Part of the PrepSense mobile app
import { View, Text, SafeAreaView, StyleSheet, TextInput, TouchableOpacity, KeyboardAvoidingView, Platform, ScrollView, StatusBar, ActivityIndicator, Alert, Image, Animated } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useState, useEffect, useRef } from 'react';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { CustomHeader } from '../components/CustomHeader';
import { sendChatMessage, Recipe, generateRecipeImage } from '../../services/api';

type Message = {
  id: string;
  text: string;
  sender: 'user' | 'ai';
  recipes?: Recipe[];
};

const suggestedMessages = [
  "What can I make for dinner?",
  "What can I make with only ingredients I have?",
  "What's good for breakfast?",
  "Show me healthy recipes",
  "Quick meals under 20 minutes",
  "What should I cook tonight?",
];

// Extended Recipe type with image URL
interface RecipeWithImage extends Recipe {
  imageUrl?: string;
}

// Recipe Card Component
function RecipeCard({ recipe, onPress }: { recipe: RecipeWithImage; onPress: () => void }) {
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [imageLoading, setImageLoading] = useState(true);

  useEffect(() => {
    // Fetch image for the recipe
    const fetchImage = async () => {
      try {
        const response = await generateRecipeImage(
          recipe.name,
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
  }, [recipe.name]);

  return (
    <TouchableOpacity style={styles.recipeCard} onPress={onPress}>
      {/* Recipe Image */}
      <View style={styles.recipeImageContainer}>
        {imageLoading ? (
          <View style={styles.imagePlaceholder}>
            <ActivityIndicator size="small" color="#297A56" />
          </View>
        ) : imageUrl ? (
          <Image source={{ uri: imageUrl }} style={styles.recipeImage} />
        ) : (
          <View style={styles.imagePlaceholder}>
            <Ionicons name="image-outline" size={30} color="#ccc" />
          </View>
        )}
      </View>

      {/* Recipe Content */}
      <View style={styles.recipeContent}>
        <Text style={styles.recipeTitle}>{recipe.name}</Text>
        <View style={styles.recipeMetrics}>
          <Text style={styles.recipeTime}>⏱️ {recipe.time} min</Text>
          <Text style={styles.recipeMatch}>
            📊 {Math.round(recipe.match_score * 100)}% match
          </Text>
          <Text style={styles.recipeEnjoyment}>
            ⭐ {recipe.expected_joy || 75}% joy
          </Text>
        </View>
        
        {recipe.available_ingredients.length > 0 && (
          <View style={styles.ingredientSection}>
            <Text style={styles.ingredientTitle}>✅ Available:</Text>
            <Text style={styles.availableIngredients} numberOfLines={2}>
              {recipe.available_ingredients.join(', ')}
            </Text>
          </View>
        )}
        
        {recipe.missing_ingredients.length > 0 && (
          <View style={styles.ingredientSection}>
            <Text style={styles.ingredientTitle}>🛒 Need to buy:</Text>
            <Text style={styles.missingIngredients} numberOfLines={2}>
              {recipe.missing_ingredients.join(', ')}
            </Text>
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
  const [showFloatingSuggestions, setShowFloatingSuggestions] = useState(false);
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const params = useLocalSearchParams();
  
  // Animation values for floating suggestions
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnims = useRef(
    suggestedMessages.map(() => new Animated.Value(-50))
  ).current;
  
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
    setShowFloatingSuggestions(false);
    await sendMessage(suggestion);
  };

  const toggleFloatingSuggestions = () => {
    const newState = !showFloatingSuggestions;
    setShowFloatingSuggestions(newState);
    
    if (newState) {
      // Animate in
      Animated.parallel([
        Animated.timing(fadeAnim, {
          toValue: 1,
          duration: 200,
          useNativeDriver: true,
        }),
        ...slideAnims.map((anim, index) =>
          Animated.timing(anim, {
            toValue: 0,
            duration: 300,
            delay: index * 50,
            useNativeDriver: true,
          })
        ),
      ]).start();
    } else {
      // Animate out
      Animated.parallel([
        Animated.timing(fadeAnim, {
          toValue: 0,
          duration: 200,
          useNativeDriver: true,
        }),
        ...slideAnims.map((anim) =>
          Animated.timing(anim, {
            toValue: -50,
            duration: 200,
            useNativeDriver: true,
          })
        ),
      ]).start();
    }
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
                  <Text style={message.sender === 'user' ? styles.userText : styles.aiText}>
                    {message.text}
                  </Text>
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
                          router.push({
                            pathname: '/recipe-details',
                            params: { recipe: JSON.stringify(recipe) }
                          });
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
      
      {/* Floating Lightbulb Button */}
      <TouchableOpacity
        style={styles.floatingLightbulb}
        onPress={toggleFloatingSuggestions}
        activeOpacity={0.8}
      >
        <Ionicons 
          name={showFloatingSuggestions ? "bulb" : "bulb-outline"} 
          size={24} 
          color="#fff" 
        />
      </TouchableOpacity>
      
      {/* Floating Suggestion Bubbles */}
      {showFloatingSuggestions && (
        <Animated.View 
          style={[
            styles.floatingSuggestionsContainer,
            { opacity: fadeAnim }
          ]}
        >
          {suggestedMessages.slice(0, 4).map((suggestion, index) => (
            <Animated.View
              key={index}
              style={[
                styles.floatingSuggestionWrapper,
                {
                  transform: [{ translateX: slideAnims[index] }]
                }
              ]}
            >
              <TouchableOpacity
                style={styles.floatingSuggestionBubble}
                onPress={() => handleSuggestedMessage(suggestion)}
                activeOpacity={0.8}
              >
                <Text style={styles.floatingSuggestionText}>{suggestion}</Text>
              </TouchableOpacity>
            </Animated.View>
          ))}
        </Animated.View>
      )}
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
  recipeEnjoyment: {
    fontSize: 12,
    color: '#F59E0B',
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
  floatingLightbulb: {
    position: 'absolute',
    bottom: 72 + 48 + 16 + 10, // TabBar height + AddButton size + margin + spacing
    right: 16, // Align with AddButton
    width: 48, // Same size as AddButton
    height: 48,
    borderRadius: 24,
    backgroundColor: '#F59E0B',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
  floatingSuggestionsContainer: {
    position: 'absolute',
    bottom: 72 + 48 + 16 + 10 - 5, // Align with lightbulb button
    right: 70,
    zIndex: 999,
  },
  floatingSuggestionWrapper: {
    marginBottom: 8,
  },
  floatingSuggestionBubble: {
    backgroundColor: '#fff',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderWidth: 1,
    borderColor: '#297A56',
    shadowColor: '#000',
    shadowOpacity: 0.1,
    shadowRadius: 8,
    shadowOffset: { width: -2, height: 2 },
    elevation: 4,
    maxWidth: 200,
  },
  floatingSuggestionText: {
    fontSize: 14,
    color: '#297A56',
    fontWeight: '500',
  },
});
