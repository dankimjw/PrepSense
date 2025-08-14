// Enhanced ESLint configuration for PrepSense React Native app
const { defineConfig } = require('eslint/config');
const expoConfig = require('eslint-config-expo/flat');
const reactHooks = require('eslint-plugin-react-hooks');
const react = require('eslint-plugin-react');
const jsxA11y = require('eslint-plugin-jsx-a11y');
const simpleImportSort = require('eslint-plugin-simple-import-sort');
const typescriptParser = require('@typescript-eslint/parser');
const typescriptPlugin = require('@typescript-eslint/eslint-plugin');

module.exports = defineConfig([
  // Base Expo config (includes import plugin)
  expoConfig,
  
  // Our enhanced configuration
  {
    languageOptions: {
      parser: typescriptParser,
      parserOptions: {
        ecmaVersion: 2020,
        sourceType: 'module',
        ecmaFeatures: {
          jsx: true,
        },
        project: './tsconfig.json',
      },
    },
    plugins: {
      'react-hooks': reactHooks,
      'react': react,
      'jsx-a11y': jsxA11y,
      'simple-import-sort': simpleImportSort,
      '@typescript-eslint': typescriptPlugin,
    },
    settings: {
      react: {
        version: 'detect',
      },
      'import/resolver': {
        typescript: {
          alwaysTryTypes: true,
          project: './tsconfig.json',
        },
        node: {
          extensions: ['.js', '.jsx', '.ts', '.tsx'],
        },
      },
    },
    rules: {
      // React Hooks rules
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'warn',
      
      // React rules - ENHANCED for catching key issues and common mistakes
      'react/react-in-jsx-scope': 'off', // Not needed with React 17+
      'react/prop-types': 'off', // Using TypeScript for prop validation
      'react/jsx-uses-react': 'off',
      'react/jsx-uses-vars': 'error',
      
      // *** KEY VALIDATION - Critical for catching duplicate key errors ***
      'react/jsx-key': [
        'error',
        {
          checkFragmentShorthand: true,
          checkKeyMustBeforeSpread: true,
          warnOnDuplicates: true,
        }
      ],
      
      // Additional React rules for enterprise standards
      'react/jsx-no-duplicate-props': 'error',
      'react/jsx-no-undef': 'error',
      'react/no-unused-state': 'warn',
      'react/no-direct-mutation-state': 'error',
      'react/jsx-curly-brace-presence': ['warn', { props: 'never', children: 'never' }],
      'react/jsx-boolean-value': ['error', 'never'],
      'react/jsx-no-useless-fragment': 'warn',
      'react/jsx-fragments': ['error', 'syntax'],
      'react/no-array-index-key': 'warn', // Warns against using array index as key
      'react/jsx-wrap-multilines': [
        'error',
        {
          declaration: 'parens-new-line',
          assignment: 'parens-new-line',
          return: 'parens-new-line',
          arrow: 'parens-new-line',
          condition: 'parens-new-line',
          logical: 'parens-new-line',
          prop: 'parens-new-line',
        },
      ],
      
      // React Native specific rules
      'react/jsx-no-target-blank': 'off', // Not applicable in React Native
      
      // TypeScript rules (using only known valid rules)
      '@typescript-eslint/no-unused-vars': [
        'error', 
        { 
          argsIgnorePattern: '^_',
          varsIgnorePattern: '^_',
          destructuredArrayIgnorePattern: '^_',
        }
      ],
      '@typescript-eslint/no-explicit-any': 'warn',
      '@typescript-eslint/no-inferrable-types': 'error',
      '@typescript-eslint/consistent-type-imports': ['error', { prefer: 'type-imports' }],
      '@typescript-eslint/no-unnecessary-type-assertion': 'error',
      '@typescript-eslint/prefer-nullish-coalescing': 'warn',
      '@typescript-eslint/prefer-optional-chain': 'warn',
      '@typescript-eslint/no-non-null-assertion': 'warn',
      '@typescript-eslint/no-unnecessary-condition': 'warn',
      
      // Import/Export rules (using existing import plugin from expo config)
      'simple-import-sort/imports': [
        'error',
        {
          groups: [
            // React and React Native imports first
            ['^react', '^react-native'],
            // Third-party packages
            ['^@?\\w'],
            // Internal packages (absolute imports)
            ['^(@|@company|@ui|components|utils|services|hooks|context|types)(/.*|$)'],
            // Relative imports
            ['^\\.\\.(?!/?$)', '^\\.\\./?$'],
            ['^\\./(?=.*/)(?!/?$)', '^\\.(?!/?$)', '^\\./?$'],
            // Style imports
            ['^.+\\.s?css$'],
          ],
        },
      ],
      'simple-import-sort/exports': 'error',
      'import/first': 'error',
      'import/newline-after-import': 'error',
      'import/no-duplicates': 'error',
      'import/no-unused-modules': 'warn',
      'import/no-cycle': 'error',
      'import/prefer-default-export': 'off',
      'import/no-anonymous-default-export': 'warn',
      
      // Accessibility rules (basic for React Native)
      'jsx-a11y/accessible-emoji': 'warn',
      'jsx-a11y/alt-text': 'warn',
      'jsx-a11y/anchor-has-content': 'off', // Not applicable in React Native
      'jsx-a11y/aria-role': 'warn',
      
      // General JavaScript/TypeScript rules - ENHANCED
      'no-console': 'off', // Allow console logs in React Native development
      'no-debugger': 'error',
      'no-duplicate-imports': 'error',
      'no-unused-expressions': 'error',
      'prefer-const': 'error',
      'no-var': 'error',
      'object-shorthand': 'error',
      'prefer-template': 'error',
      'no-template-curly-in-string': 'error',
      'array-callback-return': 'error',
      'consistent-return': 'warn',
      'no-else-return': 'warn',
      'no-implicit-coercion': 'warn',
      'no-lonely-if': 'warn',
      'no-nested-ternary': 'warn',
      'no-unneeded-ternary': 'warn',
      'no-useless-return': 'warn',
      'prefer-destructuring': [
        'warn',
        {
          array: false,
          object: true,
        },
        {
          enforceForRenamedProperties: false,
        },
      ],
      
      // Potential error prevention
      'no-await-in-loop': 'warn',
      'no-promise-executor-return': 'error',
      'no-unreachable-loop': 'error',
      'no-unused-private-class-members': 'error',
      'no-use-before-define': 'off', // Handled by TypeScript
      '@typescript-eslint/no-use-before-define': ['error', { 
        functions: false, 
        classes: true, 
        variables: true 
      }],
      
      // Styling and formatting
      'comma-dangle': ['error', 'always-multiline'],
      'quotes': ['error', 'single', { avoidEscape: true }],
      'semi': ['error', 'always'],
      'indent': ['error', 2, { SwitchCase: 1 }],
      'max-len': [
        'warn', 
        { 
          code: 100, 
          ignoreUrls: true, 
          ignoreStrings: true,
          ignoreTemplateLiterals: true,
          ignoreRegExpLiterals: true,
        }
      ],
      'object-curly-spacing': ['error', 'always'],
      'array-bracket-spacing': ['error', 'never'],
      'comma-spacing': ['error', { before: false, after: true }],
      'key-spacing': ['error', { beforeColon: false, afterColon: true }],
      'keyword-spacing': ['error', { before: true, after: true }],
      'space-before-blocks': ['error', 'always'],
      'space-infix-ops': 'error',
      
      // React Native performance rules
      'react/jsx-no-bind': [
        'warn',
        {
          ignoreRefs: true,
          allowArrowFunctions: true,
          allowFunctions: false,
          allowBind: false,
        },
      ],
    },
  },
  
  // Specific overrides for test files
  {
    files: ['**/__tests__/**/*', '**/*.test.*', '**/*.spec.*'],
    rules: {
      '@typescript-eslint/no-explicit-any': 'off',
      'no-console': 'off',
      'import/no-unused-modules': 'off',
      'react/jsx-no-bind': 'off',
      'max-len': 'off',
    },
  },
  
  // Specific overrides for configuration files
  {
    files: ['*.config.js', '*.config.ts', 'babel.config.*'],
    rules: {
      'import/no-unused-modules': 'off',
      '@typescript-eslint/no-var-requires': 'off',
      'no-console': 'off',
    },
  },
  
  // Specific overrides for component files (stricter rules)
  {
    files: ['components/**/*.{ts,tsx}', 'app/**/*.{ts,tsx}'],
    rules: {
      'react/jsx-key': [
        'error',
        {
          checkFragmentShorthand: true,
          checkKeyMustBeforeSpread: true,
          warnOnDuplicates: true,
        }
      ],
      'react/no-array-index-key': 'error', // Stricter for components
      '@typescript-eslint/no-explicit-any': 'error',
      'prefer-const': 'error',
    },
  },
]);