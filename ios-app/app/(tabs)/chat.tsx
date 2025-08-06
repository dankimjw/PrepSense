// app/chat.tsx - Part of the PrepSense mobile app
import { View, Text, StyleSheet, TextInput, TouchableOpacity, KeyboardAvoidingView, Platform, ScrollView, StatusBar, ActivityIndicator, Image } from 'react-native';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { useState, useEffect, useCallback } from 'react';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';
import { sendChatMessage, Recipe } from '../../services/api';
import Markdown from 'react-native-markdown-display';
import { useTabData } from '../../context/TabDataProvider';

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

// Extended Recipe type with image URL
interface RecipeWithImage extends Recipe {
  imageUrl?: string;
}

// Recipe Card Component - Spoonacular Style
function RecipeCard({ recipe, onPress }: { recipe: RecipeWithImage; onPress: () => void }) {
  const getRecipeImage = (): string => {
    // Use fallback image for chat recipes since they don't have Spoonacular images
    return 'https://img.spoonacular.com/recipes/default-312x231.jpg';
  };

  const getIngredientCounts = () => {
    return {
      have: recipe.available_ingredients?.length || 0,
      missing: recipe.missing_ingredients?.length || 0
    };
  };

  return (
    <View style={styles.recipeCardWrapper}>
      <TouchableOpacity
        style={styles.recipeCard}
        onPress={onPress}
        activeOpacity={0.9}
      >
        <Image 
          source={{ uri: getRecipeImage() }} 
          style={styles.recipeImage}
        />
        <LinearGradient
          colors={['transparent', 'rgba(0,0,0,0.8)']}
          style={styles.gradient}
        />
        <View style={styles.recipeInfo}>
          <Text style={styles.recipeTitle} numberOfLines={2}>
            {recipe.name}
          </Text>
          <View style={styles.recipeStats}>
            <View style={styles.stat}>
              <MaterialCommunityIcons 
                name="check-circle" 
                size={16} 
                color="#4CAF50"
              />
              <Text style={styles.statText}>{getIngredientCounts().have} have</Text>
            </View>
            <View style={styles.stat}>
              <MaterialCommunityIcons 
                name="close-circle" 
                size={16} 
                color="#F44336"
              />
              <Text style={styles.statText}>{getIngredientCounts().missing} missing</Text>
            </View>
          </View>
        </View>
      </TouchableOpacity>
    </View>
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
  const router = useRouter();
  const params = useLocalSearchParams();
  const { chatData } = useTabData();
  
  // Use preloaded suggestions if available, otherwise use defaults
  const suggestedMessages = chatData?.suggestedQuestions || defaultSuggestedMessages;
  
  const sendMessage = useCallback(async (messageText: string, withPreferences: boolean = usePreferences) => {
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
      const response = await sendChatMessage(messageText, withPreferences ? userPreferences : null);
      
      // Add AI response
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: response.response,
        sender: 'ai',
        recipes: response.recipes || [],
      };
      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: 'Sorry, I encountered an error. Please try again.',
        sender: 'ai',
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }, [isLoading, usePreferences, userPreferences]);
  
  // Check for suggestion from navigation
  useEffect(() => {
    if (params.suggestion) {
      sendMessage(params.suggestion as string);
    }
  }, [params.suggestion, sendMessage]);

  const handleSendMessage = async () => {
    if (!inputText.trim()) return;
    
    const messageText = inputText.trim();
    setInputText('');
    await sendMessage(messageText);
  };

  const handleSuggestionPress = async (suggestion: string) => {
    await sendMessage(suggestion);
  };

  const handleRecipePress = (recipe: Recipe) => {
    // Use RecipeDetailCardV3 for chat recipes
    router.push({
      pathname: '/recipe-details',
      params: { recipeData: JSON.stringify(recipe) }
    });
  };

  const renderMessage = (message: Message) => {
    if (message.sender === 'user') {
      return (
        <View key={message.id} style={styles.userMessageContainer}>
          <View style={styles.userMessage}>
            <Text style={styles.userMessageText}>{message.text}</Text>
          </View>
        </View>
      );
    } else {
      return (
        <View key={message.id} style={styles.aiMessageContainer}>
          <View style={styles.aiMessage}>
            <Markdown style={markdownStyles}>
              {message.text}
            </Markdown>
            
            {message.recipes && message.recipes.length > 0 && (
              <View style={styles.recipesContainer}>
                <Text style={styles.recipesTitle}>Recommended Recipes:</Text>
                <View style={styles.recipesGrid}>
                  {message.recipes.map((recipe, index) => (
                    <RecipeCard
                      key={`${recipe.name}-${index}`}
                      recipe={recipe}
                      onPress={() => handleRecipePress(recipe)}
                    />
                  ))}
                </View>
              </View>
            )}
          </View>
        </View>
      );
    }
  };

  const renderSuggestedMessages = () => {
    if (!showSuggestions || messages.length > 0) return null;
    
    return (
      <View style={styles.suggestionsContainer}>
        <Text style={styles.suggestionsTitle}>Try asking:</Text>
        {suggestedMessages.map((suggestion, index) => (
          <TouchableOpacity
            key={index}
            style={styles.suggestionButton}
            onPress={() => handleSuggestionPress(suggestion)}
          >
            <Text style={styles.suggestionText}>{suggestion}</Text>
          </TouchableOpacity>
        ))}
      </View>
    );
  };

  const renderPreferenceChoice = () => {
    if (!showPreferenceChoice) return null;
    
    const lastUserMessage = messages[messages.length - 2];
    if (!lastUserMessage || lastUserMessage.sender !== 'user') return null;
    
    return (
      <View style={styles.preferenceChoiceContainer}>
        <Text style={styles.preferenceChoiceTitle}>
          Would you like me to consider your dietary preferences?
        </Text>
        <View style={styles.preferenceButtons}>
          <TouchableOpacity
            style={[styles.preferenceButton, styles.yesButton]}
            onPress={() => {
              setShowPreferenceChoice(false);
              sendMessage(lastUserMessage.text, true);
            }}
          >
            <Text style={styles.preferenceButtonText}>Yes, use my preferences</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.preferenceButton, styles.noButton]}
            onPress={() => {
              setShowPreferenceChoice(false);
              sendMessage(lastUserMessage.text, false);
            }}
          >
            <Text style={styles.preferenceButtonText}>No, show all options</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  };

  return (
    <View style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor="#f8f9fa" />
      
      <KeyboardAvoidingView 
        style={styles.keyboardView}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 100 : 0}
      >
        <ScrollView 
          style={styles.messagesContainer}
          contentContainerStyle={styles.messagesContent}
          showsVerticalScrollIndicator={false}
        >
          {renderSuggestedMessages()}
          {messages.map(renderMessage)}
          {renderPreferenceChoice()}
          {isLoading && (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="small" color="#0066CC" />
              <Text style={styles.loadingText}>Thinking...</Text>
            </View>
          )}
        </ScrollView>
        
        <View style={styles.inputContainer}>
          <TextInput
            style={styles.textInput}
            value={inputText}
            onChangeText={setInputText}
            placeholder="Ask about recipes, cooking tips..."
            multiline
            maxLength={500}
            onSubmitEditing={handleSendMessage}
            returnKeyType="send"
          />
          <TouchableOpacity 
            style={[styles.sendButton, !inputText.trim() && styles.sendButtonDisabled]}
            onPress={handleSendMessage}
            disabled={!inputText.trim() || isLoading}
          >
            <Ionicons 
              name="send" 
              size={20} 
              color={inputText.trim() ? '#0066CC' : '#ccc'} 
            />
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  keyboardView: {
    flex: 1,
  },
  messagesContainer: {
    flex: 1,
    paddingHorizontal: 16,
  },
  messagesContent: {
    paddingBottom: 20,
  },
  userMessageContainer: {
    alignItems: 'flex-end',
    marginVertical: 4,
  },
  userMessage: {
    backgroundColor: '#0066CC',
    padding: 12,
    borderRadius: 18,
    maxWidth: '80%',
  },
  userMessageText: {
    color: '#fff',
    fontSize: 16,
  },
  aiMessageContainer: {
    alignItems: 'flex-start',
    marginVertical: 4,
  },
  aiMessage: {
    backgroundColor: '#fff',
    padding: 12,
    borderRadius: 18,
    maxWidth: '85%',
    borderWidth: 1,
    borderColor: '#e9ecef',
  },
  recipesContainer: {
    marginTop: 12,
  },
  recipesTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  recipesGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: 8,
  },
  // Spoonacular-style recipe card styles
  recipeCardWrapper: {
    width: '50%',
    paddingHorizontal: 8,
    marginBottom: 16,
  },
  recipeCard: {
    width: '100%',
    height: 220,
    borderRadius: 12,
    overflow: 'hidden',
    backgroundColor: '#fff',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  recipeImage: {
    width: '100%',
    height: '100%',
    resizeMode: 'cover',
  },
  gradient: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 0,
    height: 100,
  },
  recipeInfo: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    padding: 12,
  },
  recipeTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 4,
  },
  stat: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  statText: {
    fontSize: 12,
    color: '#fff',
  },
  recipeImageContainer: {
    width: 60,
    height: 60,
    borderRadius: 8,
    backgroundColor: '#e9ecef',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  imagePlaceholder: {
    width: '100%',
    height: '100%',
    justifyContent: 'center',
    alignItems: 'center',
    borderRadius: 8,
    backgroundColor: '#e9ecef',
  },
  imageLoader: {
    width: '100%',
    height: '100%',
  },
  recipeContent: {
    flex: 1,
  },
  recipeName: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
  },
  recipeStats: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
  },
  cookingTime: {
    fontSize: 12,
    color: '#666',
    marginRight: 12,
  },
  recipeMatch: {
    fontSize: 12,
    color: '#28a745',
    fontWeight: 'bold',
  },
  ingredientSection: {
    marginBottom: 4,
  },
  ingredientTitle: {
    fontSize: 11,
    fontWeight: 'bold',
    color: '#666',
    marginBottom: 2,
  },
  availableIngredients: {
    fontSize: 11,
    color: '#28a745',
  },
  missingIngredients: {
    fontSize: 11,
    color: '#dc3545',
  },
  suggestionsContainer: {
    paddingVertical: 20,
  },
  suggestionsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 16,
    textAlign: 'center',
  },
  suggestionButton: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#e9ecef',
  },
  suggestionText: {
    fontSize: 16,
    color: '#333',
  },
  preferenceChoiceContainer: {
    backgroundColor: '#fff3cd',
    padding: 16,
    borderRadius: 12,
    marginVertical: 8,
    borderWidth: 1,
    borderColor: '#ffeaa7',
  },
  preferenceChoiceTitle: {
    fontSize: 16,
    color: '#856404',
    marginBottom: 12,
    textAlign: 'center',
  },
  preferenceButtons: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  preferenceButton: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 8,
    minWidth: 120,
    alignItems: 'center',
  },
  yesButton: {
    backgroundColor: '#28a745',
  },
  noButton: {
    backgroundColor: '#6c757d',
  },
  preferenceButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
  },
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
  },
  loadingText: {
    marginLeft: 8,
    fontSize: 16,
    color: '#666',
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    padding: 16,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#e9ecef',
  },
  textInput: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#e9ecef',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
    maxHeight: 100,
    backgroundColor: '#f8f9fa',
  },
  sendButton: {
    marginLeft: 8,
    padding: 12,
    borderRadius: 20,
    backgroundColor: '#f8f9fa',
  },
  sendButtonDisabled: {
    opacity: 0.5,
  },
});

const markdownStyles = {
  body: {
    fontSize: 16,
    color: '#333',
  },
  paragraph: {
    fontSize: 16,
    color: '#333',
    marginBottom: 8,
  },
  strong: {
    fontWeight: '600' as const,
  },
  em: {
    fontStyle: 'italic' as const,
  },
  list_item: {
    fontSize: 16,
    color: '#333',
  },
};