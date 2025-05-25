# AI-Powered Checkout Automation

This module provides automated checkout functionality using Puppeteer and Google's Gemini 2.5 Flash AI. The system automates the checkout process after a user clicks the "Buy Now" button, making it seamless and convenient.

## Key Features

- **AI-Powered Form Recognition**: Uses Google's Gemini 2.5 Flash AI to analyze checkout forms and determine field mappings.
- **Intelligent Form Filling**: Automatically fills in shipping, billing, and payment information.
- **Visual Validation**: Takes screenshots of the checkout process for verification and debugging.
- **User-Friendly UI**: Provides a clean interface for monitoring the checkout process.
- **Error Handling**: Gracefully handles errors and provides clear feedback.

## Architecture

The automation system consists of several components:

1. **Frontend Integration**: Enhances the "Buy Now" buttons with AI checkout capabilities.
2. **Checkout Controller**: Express.js API for managing automation jobs.
3. **Puppeteer Automation**: Core automation engine using headless Chrome/Edge.
4. **Gemini AI Integration**: For form analysis and intelligent field mapping.

## Setup

### Prerequisites

- Node.js 16+
- npm or yarn
- Python 3.8+ (for the Flask backend)
- Google Gemini API key

### Installation

1. Run the setup script to install dependencies:
   ```
   node setup.js
   ```

2. Set your Gemini API key:
   ```
   export GEMINI_API_KEY=your-api-key
   ```
   Or add it to the `.env` file.

## Usage

### Direct Command Line Usage

Run the checkout automation directly from the command line:

```
node run_checkout.js <checkout_url> [--profile=default] [--debug]
```

Options:
- `checkout_url`: The URL of the checkout page to automate
- `--profile`: Customer profile to use (default, saved in the code)
- `--debug`: Enable verbose logging

### Programmatic Usage

```javascript
const { automateCheckout } = require('./checkout_automation');

async function runCheckout() {
  const result = await automateCheckout(
    'https://example.com/checkout?session=123',
    { title: 'Example Product', price: '$19.99' },
    'default'
  );
  
  if (result.success) {
    console.log(`Checkout completed! Order number: ${result.orderNumber}`);
  } else {
    console.error(`Checkout failed: ${result.error}`);
  }
}
```

## Adding Customer Profiles

Edit the `checkout_automation.js` file to add or modify customer profiles:

```javascript
const CUSTOMER_INFO = {
  default: {
    name: 'John Doe',
    email: 'john.doe@example.com',
    // ... other details
  },
  work: {
    name: 'John Doe',
    email: 'john.doe@company.com',
    // ... work address details
  }
};
```

## Security Considerations

- API keys and customer information are stored in code for demo purposes. In a production environment, these should be securely stored in a database or environment variables.
- Test card numbers are used for demonstration. In a production environment, integrate with a secure payment provider.
- The automation runs in a controlled environment and should not be used for unauthorized automation of websites.

## Troubleshooting

If the automation fails:

1. Check the screenshots saved in the root directory
2. Enable debug mode with the `--debug` flag
3. Verify the checkout URL is accessible
4. Ensure the Gemini API key is valid

## License

MIT 