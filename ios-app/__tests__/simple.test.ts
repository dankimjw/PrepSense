describe('Simple Test', () => {
  it('should pass basic math', () => {
    expect(1 + 1).toBe(2);
  });

  it('should handle fetch mock', () => {
    global.fetch = jest.fn();
    expect(global.fetch).toBeDefined();
  });
});