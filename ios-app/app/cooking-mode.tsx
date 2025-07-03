// app/cooking-mode.tsx - Step-by-step cooking mode for PrepSense
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  SafeAreaView,
  ScrollView,
  Alert,
  ActivityIndicator,
  Dimensions,
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Recipe, completeRecipe, RecipeIngredient } from '../services/api';
import { parseIngredientsList } from '../utils/ingredientParser';

const { width } = Dimensions.get('window');

export default function CookingModeScreen() {
  const params = useLocalSearchParams();
  const router = useRouter();
  const [recipe, setRecipe] = useState<Recipe | null>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set());
  const [isCompleting, setIsCompleting] = useState(false);
  const [activeTimer, setActiveTimer] = useState<NodeJS.Timeout | null>(null);
  const [remainingTime, setRemainingTime] = useState<number | null>(null);

  useEffect(() => {
    if (params.recipe) {
      try {
        const recipeData = JSON.parse(params.recipe as string);
        setRecipe(recipeData);
      } catch (error) {
        console.error('Error parsing recipe data:', error);
        Alert.alert('Error', 'Failed to load recipe');
        router.back();
      }
    }
  }, [params.recipe]);

  useEffect(() => {
    // Cleanup timer on unmount
    return () => {
      if (activeTimer) {
        clearInterval(activeTimer);
      }
    };
  }, [activeTimer]);

  const handlePreviousStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleNextStep = () => {
    if (recipe && currentStep < (recipe.instructions?.length || 0) - 1) {
      // Mark current step as completed
      setCompletedSteps(new Set([...completedSteps, currentStep]));
      setCurrentStep(currentStep + 1);
    }
  };

  const handleCompleteRecipe = async () => {
    Alert.alert(
      'Complete Recipe',
      'Have you finished cooking? This will remove the used ingredients from your pantry.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Yes, Complete',
          style: 'default',
          onPress: async () => {
            setIsCompleting(true);
            try {
              // Parse ingredients to extract quantities
              const parsedIngredients = parseIngredientsList(recipe.ingredients);
              
              // Convert recipe ingredients to the format needed by the API
              // For cooking mode, we assume all ingredients are available since they started cooking
              const ingredients: RecipeIngredient[] = parsedIngredients.map(parsed => ({
                ingredient_name: parsed.name,
                quantity: parsed.quantity,
                unit: parsed.unit,
              }));

              const result = await completeRecipe({
                user_id: 111, // TODO: Get actual user ID
                recipe_name: recipe.name,
                ingredients: ingredients,
              });
              
              // Handle response
              let message = `${result.summary}\n\nEnjoy your meal!`;
              
              if (result.insufficient_items && result.insufficient_items.length > 0) {
                message = `Some items had insufficient quantity but we've updated what was available.\n\n${result.summary}\n\nEnjoy your meal!`;
              }
              
              Alert.alert(
                'Recipe Completed! 🎉',
                message,
                [
                  {
                    text: 'OK',
                    onPress: () => router.back(),
                  },
                ]
              );
            } catch (error) {
              console.error('Error completing recipe:', error);
              Alert.alert('Error', 'Failed to update pantry. Please try again.');
            } finally {
              setIsCompleting(false);
            }
          },
        },
      ]
    );
  };

  const handleExit = () => {
    Alert.alert(
      'Exit Cooking Mode',
      'Are you sure you want to exit? Your progress will be lost.',
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Exit', style: 'destructive', onPress: () => {
          if (activeTimer) {
            clearInterval(activeTimer);
          }
          router.back();
        }},
      ]
    );
  };

  const parseTimeFromInstruction = (instruction: string): number | null => {
    // Match patterns like "5 minutes", "10 mins", "1 hour", etc.
    const timeMatch = instruction.match(/(\d+)\s*(minutes?|mins?|hours?|hrs?|seconds?|secs?)/i);
    
    if (!timeMatch) return null;
    
    const amount = parseInt(timeMatch[1]);
    const unit = timeMatch[2].toLowerCase();
    
    // Convert to seconds
    if (unit.startsWith('hour') || unit.startsWith('hr')) {
      return amount * 3600;
    } else if (unit.startsWith('min')) {
      return amount * 60;
    } else {
      return amount; // seconds
    }
  };

  const formatTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    } else {
      return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }
  };

  const handleSetTimer = () => {
    const timeInSeconds = parseTimeFromInstruction(recipe!.instructions![currentStep]);
    
    if (!timeInSeconds) {
      Alert.alert('Timer', 'Could not detect time from this instruction.');
      return;
    }
    
    // Clear existing timer if any
    if (activeTimer) {
      clearInterval(activeTimer);
    }
    
    setRemainingTime(timeInSeconds);
    
    const timer = setInterval(() => {
      setRemainingTime((prev) => {
        if (prev === null || prev <= 1) {
          clearInterval(timer);
          setActiveTimer(null);
          // Timer completed
          Alert.alert(
            'Timer Complete! ⏰',
            'Time is up for this step!',
            [{ text: 'OK' }]
          );
          return null;
        }
        return prev - 1;
      });
    }, 1000);
    
    setActiveTimer(timer);
  };

  const handleCancelTimer = () => {
    if (activeTimer) {
      clearInterval(activeTimer);
      setActiveTimer(null);
      setRemainingTime(null);
    }
  };

  if (!recipe || !recipe.instructions || recipe.instructions.length === 0) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>No cooking instructions available</Text>
          <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
            <Text style={styles.backButtonText}>Go Back</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  const totalSteps = recipe.instructions.length;
  const progress = ((currentStep + 1) / totalSteps) * 100;
  const isLastStep = currentStep === totalSteps - 1;

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.exitButton} onPress={handleExit}>
          <Ionicons name="close" size={28} color="#333" />
        </TouchableOpacity>
        <View style={styles.titleContainer}>
          <Text style={styles.recipeName} numberOfLines={1}>
            {recipe.name}
          </Text>
          <Text style={styles.stepIndicator}>
            Step {currentStep + 1} of {totalSteps}
          </Text>
        </View>
        <View style={styles.placeholder} />
      </View>

      {/* Progress Bar */}
      <View style={styles.progressContainer}>
        <View style={styles.progressBar}>
          <View style={[styles.progressFill, { width: `${progress}%` }]} />
        </View>
      </View>

      {/* Main Content */}
      <ScrollView 
        style={styles.content}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.stepContainer}>
          <View style={styles.stepNumberCircle}>
            <Text style={styles.stepNumber}>{currentStep + 1}</Text>
          </View>
          
          <Text style={styles.instruction}>
            {recipe.instructions[currentStep]}
          </Text>
        </View>

        {/* Timer suggestion if instruction contains time */}
        {recipe.instructions[currentStep].match(/\d+\s*(minutes?|mins?|hours?|hrs?|seconds?|secs?)/i) && !remainingTime && (
          <TouchableOpacity style={styles.timerSuggestion} onPress={handleSetTimer}>
            <Ionicons name="timer-outline" size={24} color="#297A56" />
            <Text style={styles.timerText}>Set Timer</Text>
          </TouchableOpacity>
        )}

        {/* Active timer display */}
        {remainingTime !== null && (
          <View style={styles.activeTimer}>
            <View style={styles.timerDisplay}>
              <Ionicons name="timer" size={32} color="#297A56" />
              <Text style={styles.timerCountdown}>{formatTime(remainingTime)}</Text>
            </View>
            <TouchableOpacity style={styles.cancelTimerButton} onPress={handleCancelTimer}>
              <Text style={styles.cancelTimerText}>Cancel Timer</Text>
            </TouchableOpacity>
          </View>
        )}
      </ScrollView>

      {/* Navigation Controls */}
      <View style={styles.navigationContainer}>
        <TouchableOpacity
          style={[styles.navButton, currentStep === 0 && styles.navButtonDisabled]}
          onPress={handlePreviousStep}
          disabled={currentStep === 0}
        >
          <Ionicons 
            name="chevron-back" 
            size={24} 
            color={currentStep === 0 ? '#ccc' : '#333'} 
          />
          <Text style={[styles.navButtonText, currentStep === 0 && styles.navButtonTextDisabled]}>
            Previous
          </Text>
        </TouchableOpacity>

        {isLastStep ? (
          <TouchableOpacity
            style={[styles.completeButton, isCompleting && styles.buttonDisabled]}
            onPress={handleCompleteRecipe}
            disabled={isCompleting}
          >
            {isCompleting ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <>
                <Ionicons name="checkmark-circle" size={24} color="#fff" />
                <Text style={styles.completeButtonText}>Complete</Text>
              </>
            )}
          </TouchableOpacity>
        ) : (
          <TouchableOpacity
            style={styles.navButton}
            onPress={handleNextStep}
          >
            <Text style={styles.navButtonText}>Next</Text>
            <Ionicons name="chevron-forward" size={24} color="#333" />
          </TouchableOpacity>
        )}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: 10,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  exitButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#f0f0f0',
    alignItems: 'center',
    justifyContent: 'center',
  },
  titleContainer: {
    flex: 1,
    alignItems: 'center',
    paddingHorizontal: 16,
  },
  recipeName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  stepIndicator: {
    fontSize: 14,
    color: '#666',
  },
  placeholder: {
    width: 40,
  },
  progressContainer: {
    paddingHorizontal: 20,
    paddingVertical: 12,
  },
  progressBar: {
    height: 8,
    backgroundColor: '#f0f0f0',
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#297A56',
    borderRadius: 4,
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    padding: 20,
    alignItems: 'center',
  },
  stepContainer: {
    alignItems: 'center',
    width: '100%',
    maxWidth: 400,
  },
  stepNumberCircle: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#297A56',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 24,
  },
  stepNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
  },
  instruction: {
    fontSize: 20,
    lineHeight: 32,
    textAlign: 'center',
    color: '#333',
    paddingHorizontal: 20,
  },
  timerSuggestion: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f0f7f4',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 25,
    marginTop: 24,
    gap: 8,
  },
  timerText: {
    fontSize: 16,
    color: '#297A56',
    fontWeight: '500',
  },
  navigationContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 20,
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
  },
  navButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 8,
    backgroundColor: '#f0f0f0',
    gap: 8,
  },
  navButtonDisabled: {
    opacity: 0.5,
  },
  navButtonText: {
    fontSize: 16,
    fontWeight: '500',
    color: '#333',
  },
  navButtonTextDisabled: {
    color: '#ccc',
  },
  completeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#297A56',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
    gap: 8,
  },
  completeButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  errorText: {
    fontSize: 18,
    color: '#666',
    marginBottom: 20,
  },
  backButton: {
    backgroundColor: '#297A56',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
  },
  backButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  activeTimer: {
    backgroundColor: '#f0f7f4',
    padding: 20,
    borderRadius: 12,
    marginTop: 24,
    alignItems: 'center',
  },
  timerDisplay: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 12,
  },
  timerCountdown: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#297A56',
  },
  cancelTimerButton: {
    backgroundColor: '#fff',
    paddingHorizontal: 20,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#297A56',
  },
  cancelTimerText: {
    color: '#297A56',
    fontSize: 14,
    fontWeight: '500',
  },
});