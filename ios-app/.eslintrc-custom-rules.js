/**
 * Custom ESLint Rules for PrepSense React Native App
 * Includes specific rules to catch React key issues and other common problems
 */

module.exports = {
  rules: {
    // Custom rule to catch potential undefined key issues
    'no-undefined-keys': {
      meta: {
        type: 'error',
        docs: {
          description: 'Prevent using potentially undefined values as React keys',
          category: 'Best Practices',
          recommended: true,
        },
        schema: [],
        messages: {
          undefinedKey: 'Potential undefined key detected: "{{keyValue}}". Use fallback like "key={item.id || `fallback-${index}`}"',
          stringTemplateKey: 'Using string template with potentially undefined value in key: "{{keyValue}}". Ensure the value is always defined.',
        },
      },
      create(context) {
        return {
          JSXAttribute(node) {
            // Only check 'key' attributes
            if (node.name.name !== 'key') return;

            const keyValue = node.value;
            
            // Check for JSX expressions
            if (keyValue && keyValue.type === 'JSXExpressionContainer') {
              const expression = keyValue.expression;
              
              // Check for direct property access that might be undefined (item.id)
              if (expression.type === 'MemberExpression') {
                const propertyName = expression.property.name;
                if (propertyName === 'id' || propertyName.includes('id')) {
                  // Look for common patterns that suggest the value might be undefined
                  const source = context.getSourceCode().getText(expression);
                  context.report({
                    node: keyValue,
                    messageId: 'undefinedKey',
                    data: {
                      keyValue: source,
                    },
                  });
                }
              }
              
              // Check for template literals with potentially undefined values
              if (expression.type === 'TemplateLiteral') {
                const source = context.getSourceCode().getText(expression);
                if (source.includes('${') && source.includes('.id')) {
                  context.report({
                    node: keyValue,
                    messageId: 'stringTemplateKey',
                    data: {
                      keyValue: source,
                    },
                  });
                }
              }
            }
          },
        };
      },
    },

    // Custom rule to ensure proper key generation in map functions
    'proper-map-keys': {
      meta: {
        type: 'error',
        docs: {
          description: 'Ensure proper key generation in array map functions',
          category: 'Best Practices',
          recommended: true,
        },
        schema: [],
        messages: {
          missingKey: 'Array map without proper key detected. Add unique key prop to JSX elements.',
          indexAsKey: 'Using array index as key. Consider using a unique identifier instead.',
          potentialDuplicateKey: 'Potential duplicate keys detected. Ensure key values are unique.',
        },
      },
      create(context) {
        return {
          CallExpression(node) {
            // Check for .map() calls
            if (
              node.callee.type === 'MemberExpression' &&
              node.callee.property.name === 'map'
            ) {
              // Check if the callback returns JSX
              const callback = node.arguments[0];
              if (callback && (callback.type === 'ArrowFunctionExpression' || callback.type === 'FunctionExpression')) {
                const callbackBody = callback.body;
                
                // If returning JSX directly (arrow function without braces)
                if (callbackBody.type === 'JSXElement' || callbackBody.type === 'JSXFragment') {
                  this.checkJSXForKey(context, callbackBody, callback.params);
                }
                
                // If return statement in block
                if (callbackBody.type === 'BlockStatement') {
                  callbackBody.body.forEach((stmt) => {
                    if (stmt.type === 'ReturnStatement' && stmt.argument) {
                      if (stmt.argument.type === 'JSXElement' || stmt.argument.type === 'JSXFragment') {
                        this.checkJSXForKey(context, stmt.argument, callback.params);
                      }
                    }
                  });
                }
              }
            }
          },
          
          checkJSXForKey(context, jsxNode, params) {
            if (jsxNode.type === 'JSXElement') {
              const keyAttr = jsxNode.openingElement.attributes.find(
                (attr) => attr.type === 'JSXAttribute' && attr.name.name === 'key'
              );
              
              if (!keyAttr) {
                context.report({
                  node: jsxNode,
                  messageId: 'missingKey',
                });
              } else {
                // Check if using index as key
                const keyValue = keyAttr.value;
                if (keyValue && keyValue.type === 'JSXExpressionContainer') {
                  const expression = keyValue.expression;
                  
                  // Check for index parameter being used as key
                  if (expression.type === 'Identifier' && params.length > 1) {
                    const indexParam = params[1];
                    if (indexParam && indexParam.name === expression.name) {
                      context.report({
                        node: keyAttr,
                        messageId: 'indexAsKey',
                      });
                    }
                  }
                }
              }
            }
          },
        };
      },
    },

    // Custom rule to detect console.error patterns that suggest React warnings
    'detect-react-warnings': {
      meta: {
        type: 'warning',
        docs: {
          description: 'Detect patterns that commonly cause React warnings',
          category: 'Best Practices',
          recommended: true,
        },
        schema: [],
        messages: {
          potentialKeyWarning: 'Code pattern may cause React key warnings. Ensure all items in arrays have unique keys.',
        },
      },
      create(context) {
        return {
          CallExpression(node) {
            // Look for console.error calls
            if (
              node.callee.type === 'MemberExpression' &&
              node.callee.object.name === 'console' &&
              node.callee.property.name === 'error'
            ) {
              // Check if error message mentions keys
              if (node.arguments.length > 0) {
                const firstArg = node.arguments[0];
                if (firstArg.type === 'Literal' && typeof firstArg.value === 'string') {
                  const errorMessage = firstArg.value.toLowerCase();
                  if (errorMessage.includes('same key') || errorMessage.includes('unique')) {
                    context.report({
                      node,
                      messageId: 'potentialKeyWarning',
                    });
                  }
                }
              }
            }
          },
        };
      },
    },
  },
};