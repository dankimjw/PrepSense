import React, { memo, useEffect, useState, useCallback } from 'react';
import {
  Modal,
  View,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  InteractionManager,
  Dimensions,
} from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withTiming,
  withSpring,
  runOnJS,
  interpolate,
  Extrapolate,
} from 'react-native-reanimated';
import { performanceMonitor } from '../../utils/performanceMonitoring';
import { useDeferredOperation } from '../../hooks/useDeferredOperation';

const { height: screenHeight } = Dimensions.get('window');

interface OptimizedModalProps {
  visible: boolean;
  onClose: () => void;
  children: React.ReactNode;
  animationType?: 'fade' | 'slide' | 'none';
  lazy?: boolean;
  preload?: boolean;
  onModalShow?: () => void;
  onModalHide?: () => void;
  testID?: string;
}

const ModalContent = memo(({ children }: { children: React.ReactNode }) => {
  return <>{children}</>;
});

export const OptimizedModal = memo<OptimizedModalProps>(({
  visible,
  onClose,
  children,
  animationType = 'slide',
  lazy = true,
  preload = false,
  onModalShow,
  onModalHide,
  testID,
}) => {
  const [contentReady, setContentReady] = useState(!lazy || preload);
  const [modalVisible, setModalVisible] = useState(visible);
  const { runDeferred } = useDeferredOperation();
  
  // Animation values
  const backdropOpacity = useSharedValue(0);
  const contentTranslateY = useSharedValue(animationType === 'slide' ? screenHeight : 0);
  const contentOpacity = useSharedValue(animationType === 'fade' ? 0 : 1);
  const contentScale = useSharedValue(0.95);

  // Performance tracking
  useEffect(() => {
    if (visible) {
      const perfLabel = `modal-open-${testID || 'unknown'}`;
      performanceMonitor.startMeasure(perfLabel);
      
      return () => {
        const duration = performanceMonitor.endMeasure(perfLabel);
        if (duration > 300) {
          console.warn(`[Performance] Modal open animation took ${duration.toFixed(0)}ms`);
        }
      };
    }
  }, [visible, testID]);

  // Handle visibility changes
  useEffect(() => {
    if (visible) {
      setModalVisible(true);
      
      // Load content if lazy
      if (lazy && !contentReady) {
        runDeferred(() => {
          setContentReady(true);
        }, { priority: 'high' });
      }

      // Animate in
      InteractionManager.runAfterInteractions(() => {
        backdropOpacity.value = withTiming(1, { duration: 200 });
        
        if (animationType === 'slide') {
          contentTranslateY.value = withSpring(0, {
            damping: 25,
            stiffness: 200,
          });
        } else if (animationType === 'fade') {
          contentOpacity.value = withTiming(1, { duration: 200 });
          contentScale.value = withSpring(1, {
            damping: 20,
            stiffness: 180,
          });
        }

        if (onModalShow) {
          runOnJS(onModalShow)();
        }
      });
    } else {
      // Animate out
      backdropOpacity.value = withTiming(0, { duration: 150 });
      
      if (animationType === 'slide') {
        contentTranslateY.value = withTiming(screenHeight, { duration: 200 }, (finished) => {
          if (finished) {
            runOnJS(() => {
              setModalVisible(false);
              if (lazy) {
                setContentReady(false);
              }
              if (onModalHide) {
                onModalHide();
              }
            })();
          }
        });
      } else if (animationType === 'fade') {
        contentOpacity.value = withTiming(0, { duration: 150 });
        contentScale.value = withTiming(0.95, { duration: 150 }, (finished) => {
          if (finished) {
            runOnJS(() => {
              setModalVisible(false);
              if (lazy) {
                setContentReady(false);
              }
              if (onModalHide) {
                onModalHide();
              }
            })();
          }
        });
      } else {
        setModalVisible(false);
        if (lazy) {
          setContentReady(false);
        }
        if (onModalHide) {
          onModalHide();
        }
      }
    }
  }, [visible, lazy, contentReady, animationType, onModalShow, onModalHide, runDeferred]);

  const backdropStyle = useAnimatedStyle(() => ({
    opacity: backdropOpacity.value,
  }));

  const contentStyle = useAnimatedStyle(() => {
    if (animationType === 'slide') {
      return {
        transform: [{ translateY: contentTranslateY.value }],
      };
    } else if (animationType === 'fade') {
      return {
        opacity: contentOpacity.value,
        transform: [{ scale: contentScale.value }],
      };
    }
    return {};
  });

  const handleBackdropPress = useCallback(() => {
    onClose();
  }, [onClose]);

  if (!modalVisible) {
    return null;
  }

  return (
    <Modal
      visible={modalVisible}
      transparent
      animationType="none"
      statusBarTranslucent
      onRequestClose={onClose}
      testID={testID}
    >
      <View style={styles.container}>
        {/* Backdrop */}
        <Animated.View style={[styles.backdrop, backdropStyle]}>
          <TouchableOpacity
            style={StyleSheet.absoluteFillObject}
            onPress={handleBackdropPress}
            activeOpacity={1}
          />
        </Animated.View>

        {/* Content */}
        <Animated.View
          style={[
            styles.content,
            animationType !== 'none' && contentStyle,
          ]}
          pointerEvents="box-none"
        >
          {contentReady ? (
            <ModalContent>{children}</ModalContent>
          ) : (
            <View style={styles.loader}>
              <ActivityIndicator size="large" color="#297A56" />
            </View>
          )}
        </Animated.View>
      </View>
    </Modal>
  );
});

OptimizedModal.displayName = 'OptimizedModal';

// HOC for easy migration
export const withOptimizedModal = <P extends object>(
  Component: React.ComponentType<P>,
  modalOptions?: Partial<OptimizedModalProps>
) => {
  return memo((props: P & Pick<OptimizedModalProps, 'visible' | 'onClose'>) => {
    const { visible, onClose, ...componentProps } = props;
    
    return (
      <OptimizedModal
        visible={visible}
        onClose={onClose}
        {...modalOptions}
      >
        <Component {...(componentProps as P)} />
      </OptimizedModal>
    );
  });
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  backdrop: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
  },
  content: {
    flex: 1,
    justifyContent: 'flex-end',
  },
  loader: {
    backgroundColor: 'white',
    padding: 20,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    alignItems: 'center',
    minHeight: 200,
    justifyContent: 'center',
  },
});