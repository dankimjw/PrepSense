// Basic test to verify hybrid components can be imported and used
import React from 'react';

describe('Hybrid Components Basic Tests', () => {
  it('can import HybridTextInput', () => {
    const { HybridTextInput } = require('../../../components/hybrid/HybridTextInput');
    expect(HybridTextInput).toBeDefined();
  });

  it('can import SearchBarHybrid', () => {
    const { SearchBarHybrid } = require('../../../components/SearchBarHybrid');
    expect(SearchBarHybrid).toBeDefined();
  });

  it('can import AddItemModalV2Hybrid', () => {
    const { AddItemModalV2Hybrid } = require('../../../components/modals/AddItemModalV2Hybrid');
    expect(AddItemModalV2Hybrid).toBeDefined();
  });

  it('can import debug helpers', () => {
    const { debugBorder, debugLog, debugHybrid, debugRenderTime } = require('../../../components/debug/DebugPanel');
    expect(debugBorder).toBeDefined();
    expect(debugLog).toBeDefined();
    expect(debugHybrid).toBeDefined();
    expect(debugRenderTime).toBeDefined();
  });

  it('can import hybrid theme and provider', () => {
    const { lightTheme, darkTheme, getTheme } = require('../../../config/hybridTheme');
    const { HybridProvider, StyleDebugger } = require('../../../config/hybridProvider');
    
    expect(lightTheme).toBeDefined();
    expect(darkTheme).toBeDefined();
    expect(getTheme).toBeDefined();
    expect(HybridProvider).toBeDefined();
    expect(StyleDebugger).toBeDefined();
  });
});