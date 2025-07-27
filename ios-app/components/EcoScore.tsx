import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

interface EcoScoreProps {
  score: 'A' | 'B' | 'C' | 'D' | 'E';
  size?: 'small' | 'medium' | 'large';
  showLabel?: boolean;
}

const EcoScore: React.FC<EcoScoreProps> = ({ score, size = 'medium', showLabel = true }) => {
  const getScoreColor = () => {
    switch (score) {
      case 'A':
        return '#047857'; // Dark green
      case 'B':
        return '#10b981'; // Green
      case 'C':
        return '#f59e0b'; // Yellow
      case 'D':
        return '#f97316'; // Orange
      case 'E':
        return '#dc2626'; // Red
      default:
        return '#6b7280'; // Gray
    }
  };

  const getSizeStyles = () => {
    switch (size) {
      case 'small':
        return {
          container: { width: 30, height: 30 },
          text: { fontSize: 16 },
          label: { fontSize: 10 }
        };
      case 'large':
        return {
          container: { width: 60, height: 60 },
          text: { fontSize: 32 },
          label: { fontSize: 14 }
        };
      default: // medium
        return {
          container: { width: 45, height: 45 },
          text: { fontSize: 24 },
          label: { fontSize: 12 }
        };
    }
  };

  const color = getScoreColor();
  const sizeStyles = getSizeStyles();

  return (
    <View style={styles.wrapper}>
      <View style={[
        styles.container,
        sizeStyles.container,
        { backgroundColor: color }
      ]}>
        <Text style={[styles.scoreText, sizeStyles.text]}>
          {score}
        </Text>
      </View>
      {showLabel && (
        <Text style={[styles.label, sizeStyles.label]}>
          Eco-Score
        </Text>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  wrapper: {
    alignItems: 'center',
  },
  container: {
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  scoreText: {
    color: 'white',
    fontWeight: 'bold',
  },
  label: {
    marginTop: 4,
    color: '#6b7280',
  },
});

export default EcoScore;