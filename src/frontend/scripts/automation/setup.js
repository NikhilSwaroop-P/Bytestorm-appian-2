#!/usr/bin/env node
/**
 * Setup Script for Checkout Automation
 * 
 * This script installs the necessary dependencies for the checkout automation.
 */

const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

// Define dependencies
const dependencies = {
  puppeteer: '^21.0.0',
  '@google/generative-ai': '^0.2.0',
  'express': '^4.18.2',
  'body-parser': '^1.20.2',
  'cors': '^2.8.5'
};

// Colors for console output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  red: '\x1b[31m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
  magenta: '\x1b[35m'
};

console.log(`${colors.blue}=====================================${colors.reset}`);
console.log(`${colors.blue}  Checkout Automation Setup  ${colors.reset}`);
console.log(`${colors.blue}=====================================${colors.reset}`);

// Define the package.json location
const packageJsonPath = path.join(__dirname, '..', '..', '..', '..', 'package.json');
let packageJson;

// Check if package.json exists
try {
  packageJson = require(packageJsonPath);
  console.log(`${colors.green}✓${colors.reset} Found package.json`);
} catch (error) {
  console.log(`${colors.yellow}!${colors.reset} package.json not found, creating new one`);
  packageJson = {
    name: 'checkout-automation-agent',
    version: '1.0.0',
    description: 'AI-powered checkout automation agent using Puppeteer',
    main: 'src/checkout_agent.js',
    scripts: {
      start: 'node src/checkout_agent.js',
      test: 'echo "Error: no test specified" && exit 1'
    },
    dependencies: {},
    author: '',
    license: 'MIT'
  };
}

// Ensure dependencies section exists
if (!packageJson.dependencies) {
  packageJson.dependencies = {};
}

// Check which dependencies need to be installed
const missingDeps = [];
for (const [dep, version] of Object.entries(dependencies)) {
  if (!packageJson.dependencies[dep]) {
    missingDeps.push(`${dep}@${version}`);
    packageJson.dependencies[dep] = version;
    console.log(`${colors.yellow}!${colors.reset} Will install ${colors.cyan}${dep}@${version}${colors.reset}`);
  } else {
    console.log(`${colors.green}✓${colors.reset} ${colors.cyan}${dep}${colors.reset} is already installed`);
  }
}

// Add scripts for checkout automation if they don't exist
if (!packageJson.scripts) {
  packageJson.scripts = {};
}

// Add checkout automation scripts
if (!packageJson.scripts['checkout']) {
  packageJson.scripts['checkout'] = 'node src/frontend/scripts/automation/run_checkout.js';
  console.log(`${colors.yellow}!${colors.reset} Added ${colors.cyan}checkout${colors.reset} script`);
}

if (!packageJson.scripts['checkout:debug']) {
  packageJson.scripts['checkout:debug'] = 'node src/frontend/scripts/automation/run_checkout.js --debug';
  console.log(`${colors.yellow}!${colors.reset} Added ${colors.cyan}checkout:debug${colors.reset} script`);
}

// Save updated package.json
fs.writeFileSync(packageJsonPath, JSON.stringify(packageJson, null, 2));
console.log(`${colors.green}✓${colors.reset} Updated package.json`);

// Install missing dependencies if any
if (missingDeps.length > 0) {
  console.log(`${colors.blue}=====================================${colors.reset}`);
  console.log(`${colors.blue}  Installing Dependencies  ${colors.reset}`);
  console.log(`${colors.blue}=====================================${colors.reset}`);
  console.log(`${colors.yellow}!${colors.reset} Installing ${missingDeps.length} package(s)...`);
  
  try {
    execSync(`npm install ${missingDeps.join(' ')}`, { stdio: 'inherit' });
    console.log(`${colors.green}✓${colors.reset} All dependencies installed successfully`);
  } catch (error) {
    console.error(`${colors.red}✗${colors.reset} Error installing dependencies:`);
    console.error(error.message);
    process.exit(1);
  }
} else {
  console.log(`${colors.green}✓${colors.reset} All dependencies are already installed`);
}

// Create a .env file for the API key if it doesn't exist
const envPath = path.join(__dirname, '..', '..', '..', '..', '.env');
if (!fs.existsSync(envPath)) {
  console.log(`${colors.yellow}!${colors.reset} Creating .env file for API key`);
  fs.writeFileSync(envPath, 'GEMINI_API_KEY=AIzaSyCDTRtFFd62Xv7YGvr3ksNYeeFvQycACP8\n');
} else {
  // Check if the API key is already in the .env file
  const envContent = fs.readFileSync(envPath, 'utf8');
  if (!envContent.includes('GEMINI_API_KEY=')) {
    console.log(`${colors.yellow}!${colors.reset} Adding Gemini API key to .env file`);
    fs.appendFileSync(envPath, '\nGEMINI_API_KEY=AIzaSyCDTRtFFd62Xv7YGvr3ksNYeeFvQycACP8\n');
  } else {
    console.log(`${colors.green}✓${colors.reset} Gemini API key already in .env file`);
  }
}

console.log(`${colors.blue}=====================================${colors.reset}`);
console.log(`${colors.green}  Setup Complete!  ${colors.reset}`);
console.log(`${colors.blue}=====================================${colors.reset}`);
console.log(`To run the automated checkout:`);
console.log(`${colors.cyan}npm run checkout <checkout_url>${colors.reset}`);
console.log(`${colors.blue}=====================================${colors.reset}`); 