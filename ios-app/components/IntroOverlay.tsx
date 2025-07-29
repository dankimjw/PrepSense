import React, { useEffect, useState } from 'react';
import { View, StyleSheet, Modal, Platform } from 'react-native';
import IntroScreen from './IntroScreen';

interface IntroOverlayProps {
  visible: boolean;
  onFinished: () => void;
}

const IntroOverlay: React.FC<IntroOverlayProps> = ({ visible, onFinished }) => {
  const [shouldShow, setShouldShow] = useState(visible);

  useEffect(() => {
    if (visible && !shouldShow) {
      setShouldShow(true);
    }
  }, [visible]);

  const handleFinished = () => {
    setShouldShow(false);
    onFinished();
  };

  // Handle keyboard shortcuts (Cmd+Enter)
  useEffect(() => {
    if (!visible) return;

    const handleKeyPress = (event: KeyboardEvent) => {
      if (Platform.OS === 'web') {
        // For web testing - detect Cmd+Enter
        if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
          event.preventDefault();
          handleFinished();
        }
      }
    };

    if (Platform.OS === 'web') {
      document.addEventListener('keydown', handleKeyPress);
      return () => {
        document.removeEventListener('keydown', handleKeyPress);
      };
    }
  }, [visible]);

  return (
    <Modal
      visible={shouldShow}
      animationType="fade"
      presentationStyle="fullScreen"
      statusBarHidden={true}
    >
      <View style={styles.container}>
        <IntroScreen onFinished={handleFinished} />
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
});

export default IntroOverlay;