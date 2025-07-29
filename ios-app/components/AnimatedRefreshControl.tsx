import React from 'react';
import { RefreshControl } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedProps,
  withSpring,
  interpolate,
} from 'react-native-reanimated';

const AnimatedRefreshControlComponent = Animated.createAnimatedComponent(RefreshControl);

interface AnimatedRefreshControlProps {
  refreshing: boolean;
  onRefresh: () => void;
}

const AnimatedRefreshControl: React.FC<AnimatedRefreshControlProps> = ({
  refreshing,
  onRefresh,
}) => {
  const progress = useSharedValue(0);

  const animatedProps = useAnimatedProps(() => {
    return {
      progressViewOffset: interpolate(
        progress.value,
        [0, 1],
        [0, 20]
      ),
    };
  });

  React.useEffect(() => {
    progress.value = withSpring(refreshing ? 1 : 0, {
      damping: 15,
      stiffness: 150,
    });
  }, [refreshing]);

  return (
    <AnimatedRefreshControlComponent
      refreshing={refreshing}
      onRefresh={onRefresh}
      tintColor="#297A56"
      colors={['#297A56']}
      animatedProps={animatedProps}
    />
  );
};

export default AnimatedRefreshControl;