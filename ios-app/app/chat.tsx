// app/chat.tsx - Part of the PrepSense mobile app
import { View, Text, SafeAreaView, StyleSheet, TextInput, TouchableOpacity, KeyboardAvoidingView, Platform, ScrollView, StatusBar, ActivityIndicator, Alert } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useState } from 'react';
import { CustomHeader } from './components/CustomHeader';
import { sendChatMessage, Recipe } from '../services/api';

type Message = {
  id: string;
  text: string;
  sender: 'user' | 'ai';
  recipes?: Recipe[];
};

export default function ChatScreen() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const insets = useSafeAreaInsets();

  const handleSend = async () => {
    if (inputText.trim() === '' || isLoading) return;
    
    const messageText = inputText.trim();
    setInputText('');
    setIsLoading(true);
    
    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      text: messageText,
      sender: 'user',
    };
    
    setMessages(prev => [...prev, userMessage]);
    
    try {
      // Call the actual API
      const response = await sendChatMessage(messageText);
      
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

  return (
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
                
                {/* Show recipe cards for AI messages with recipes */}
                {message.sender === 'ai' && message.recipes && message.recipes.length > 0 && (
                  <View style={styles.recipesContainer}>
                    {message.recipes.map((recipe, index) => (
                      <View key={index} style={styles.recipeCard}>
                        <Text style={styles.recipeTitle}>{recipe.name}</Text>
                        <Text style={styles.recipeTime}>⏱️ {recipe.time} minutes</Text>
                        <Text style={styles.recipeMatch}>
                          📊 {Math.round(recipe.match_score * 100)}% match
                        </Text>
                        
                        {recipe.available_ingredients.length > 0 && (
                          <View style={styles.ingredientSection}>
                            <Text style={styles.ingredientTitle}>✅ Available:</Text>
                            <Text style={styles.availableIngredients}>
                              {recipe.available_ingredients.join(', ')}
                            </Text>
                          </View>
                        )}
                        
                        {recipe.missing_ingredients.length > 0 && (
                          <View style={styles.ingredientSection}>
                            <Text style={styles.ingredientTitle}>🛒 Need to buy:</Text>
                            <Text style={styles.missingIngredients}>
                              {recipe.missing_ingredients.join(', ')}
                            </Text>
                          </View>
                        )}
                        
                        <View style={styles.nutritionRow}>
                          <Text style={styles.nutritionText}>
                            🔥 {recipe.nutrition.calories} cal
                          </Text>
                          <Text style={styles.nutritionText}>
                            💪 {recipe.nutrition.protein}g protein
                          </Text>
                        </View>
                      </View>
                    ))}
                  </View>
                )}
              </View>
            ))
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
    padding: 16,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#e0e0e0',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 2,
  },
  recipeTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  recipeTime: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  recipeMatch: {
    fontSize: 14,
    color: '#297A56',
    fontWeight: '600',
    marginBottom: 12,
  },
  ingredientSection: {
    marginBottom: 8,
  },
  ingredientTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  availableIngredients: {
    fontSize: 14,
    color: '#297A56',
    lineHeight: 20,
  },
  missingIngredients: {
    fontSize: 14,
    color: '#DC2626',
    lineHeight: 20,
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
});
