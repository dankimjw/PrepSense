# Jest Async Testing Lessons Learned

## Critical Mistake: Blaming Infrastructure Instead of Knowledge Gap

### What I Said Wrong
- "async timing issues in the test infrastructure" ❌
- "Test infrastructure needs better handling" ❌
- Suggested the testing tools were flawed

### The Reality
- Jest and React Native Testing Library are battle-tested and well-designed
- The "infrastructure" works perfectly fine
- The problem was my lack of knowledge about proper testing patterns

## Correct Async Testing Patterns

### 1. Use `waitFor` for Async State Updates
```javascript
// ❌ WRONG - Expecting immediate updates
fireEvent.press(button);
expect(getByText('Updated')).toBeTruthy(); // Fails

// ✅ CORRECT - Wait for async updates
fireEvent.press(button);
await waitFor(() => {
  expect(getByText('Updated')).toBeTruthy();
});
```

### 2. Never Use Arbitrary Delays
```javascript
// ❌ WRONG - Fixed delays are flaky
await sleep(100);
expect(something).toBeTruthy();

// ✅ CORRECT - waitFor adapts to actual timing
await waitFor(() => {
  expect(something).toBeTruthy();
});
```

### 3. Handle Multiple Elements
```javascript
// ❌ WRONG - getByText fails with multiple matches
expect(getByText('Use: 1 cup')).toBeTruthy();

// ✅ CORRECT - Use getAllByText when expecting multiple
const elements = getAllByText('Use: 1 cup');
expect(elements.length).toBeGreaterThan(0);
```

## Key Principles

1. **Trust the Tools** - Jest and RNTL are production-ready
2. **Learn Before Blaming** - Research proper patterns before assuming tools are broken
3. **Read the Docs** - Context7 MCP server provides excellent documentation
4. **Admit Knowledge Gaps** - "I don't know the proper pattern" is better than "the infrastructure is broken"

## Slider Testing Reality

I incorrectly claimed sliders couldn't be tested. They CAN be tested:
- React Native Slider components can receive `onValueChange` events
- The issue was not having proper testIDs and using the right queries
- Could have used `fireEvent.valueChange(slider, newValue)`

## Better Responses

Instead of: "The test infrastructure has async timing issues"
Say: "I need to learn the proper async testing patterns in Jest"

Instead of: "Sliders can't be tested in Jest"
Say: "I'm not sure how to test sliders properly, let me research"

## References
- Jest Timer Mocks: https://jestjs.io/docs/timer-mocks
- RNTL Async Utilities: https://callstack.github.io/react-native-testing-library/docs/api/async
- waitFor API: Retries assertion until it passes or times out