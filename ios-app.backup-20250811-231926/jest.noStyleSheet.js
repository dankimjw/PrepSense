// Alternative jest setup that completely bypasses StyleSheet
// by making it a simple pass-through function

// Override StyleSheet at the global level before anything else
global.StyleSheet = {
  create: (styles) => styles,
  flatten: (style) => style,
  hairlineWidth: 1,
  absoluteFill: { position: 'absolute', left: 0, right: 0, top: 0, bottom: 0 },
  absoluteFillObject: { position: 'absolute', left: 0, right: 0, top: 0, bottom: 0 },
};

// Override PixelRatio
global.PixelRatio = {
  get: () => 2,
  getFontScale: () => 1,
  getPixelSizeForLayoutSize: (layoutSize) => layoutSize * 2,
  roundToNearestPixel: (layoutSize) => Math.round(layoutSize),
};

// Override Dimensions
global.Dimensions = {
  get: () => ({ width: 390, height: 844, scale: 3, fontScale: 1 }),
  addEventListener: () => {},
  removeEventListener: () => {},
};

// Override Platform
global.Platform = {
  OS: 'ios',
  Version: '14.0',
  select: (obj) => obj.ios || obj.default,
  isPad: false,
  isTesting: true,
  isTV: false,
};

// Mock React Native at the module level BEFORE any imports
const moduleMap = new Map();

const originalRequire = require;
require = function(id) {
  if (id === 'react-native' || id.includes('react-native/Libraries/StyleSheet')) {
    if (moduleMap.has(id)) {
      return moduleMap.get(id);
    }
    
    const RN = originalRequire.call(this, 'react-native');
    const mockedRN = {
      ...RN,
      StyleSheet: global.StyleSheet,
      PixelRatio: global.PixelRatio,
      Dimensions: global.Dimensions,
      Platform: global.Platform,
    };
    
    moduleMap.set(id, mockedRN);
    return mockedRN;
  }
  
  return originalRequire.apply(this, arguments);
};

console.log('✅ StyleSheet bypass setup complete');