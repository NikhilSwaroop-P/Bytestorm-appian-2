# AI-Powered Product Discovery and Checkout Pipeline
![pipeline_visualization](https://github.com/user-attachments/assets/eef8fac9-6cdc-44fb-aaf0-1d89e94528b8)

## Project Overview

This project implements an advanced AI-driven product discovery and checkout system that enables users to search for products using both text queries and images. The pipeline integrates computer vision, natural language processing, and search techniques to create a seamless shopping experience from initial product discovery to final checkout.

## Core Architecture

The system is built around a modular pipeline architecture with specialized blocks handling different aspects of the search and checkout process:

1. **Query Processing**: Analyzes and transforms user text inputs
2. **Image Analysis**: Extracts product features from uploaded images
3. **Retrieval System**: Finds relevant products using multi-modal search
4. **Filtering Engine**: Applies special case filters based on specific criteria
5. **UI Components**: Provides intuitive user interfaces for the search process
6. **AI Checkout**: Automates the checkout process with minimal user interaction

## Key Components

### Query Processing
- Splits user queries into general and special components
- Handles special cases like brands, colors, and attributes
- Updates current search context with new query information
- Performs conflict detection between queries and current context

### Image Processing
- Detects user intent from uploaded images
- Extracts detailed product descriptions from images
- Modifies text queries based on image content
- Splits text into backbone and descriptive components
- Balances text and image weights based on query intent

### Retrieval System
- Combines image and text-based search techniques
- Implements a specialized reranking system for better relevance
- Uses a backbone-based retrieval with fine-tuning from current context
- Optimizes search in conflict scenarios with specialized retrieval

### Filtering Engine
- Applies special case filters for attributes like brand, color, and size
- Extracts and attaches tags to search results
- Implements fast filtering based on parsed query specifications
- Returns optimized results with metadata and tags

### UI Components
- Text query input for traditional search
- Image upload capability for visual search
- Reset functionality for starting new searches
- Results display with product grid and tag visualization
- Refinement options based on extracted features

### AI Checkout
- Analyzes user images and text to identify product intent
- Extracts key product features (brand, color, size)
- Matches with exact products in the database
- Implements confidence-based verification system
- Provides automatic checkout with minimal user interaction

## Technologies and Methods

- **Computer Vision**: For image analysis and feature extraction
- **Natural Language Processing**: For query understanding and manipulation
- **Vector Search**: For efficient multi-modal retrieval
- **Semantic Reranking**: For improving search relevance
- **Special Case Handling**: For managing specific user requests
- **Confidence Scoring**: For determining when to verify with users

## Key Features

- **Multi-modal Search**: Combine text and image inputs for better results
- **Progressive Refinement**: Build upon previous searches with new queries
- **Special Case Handling**: Support for specific attribute filtering
- **Intent Detection**: Understand user intentions from images and text
- **Automated Checkout**: Streamline purchasing with AI assistance
- **Tag Extraction**: Identify and highlight key product attributes

## Implementation Details

The system maintains state through key variables:
- `current_text`: The active search query
- `back_bone`: The core product type being searched
- `retrieved_idx`: Indices of retrieved products
- `meta`: Metadata for search results
- `img_weight` and `text_weight`: Balance between image and text search

The pipeline processes inputs through a series of specialized modules that analyze, transform, and filter data to produce increasingly refined results, ultimately leading to product selection and checkout.

## User Experience Flow

1. User uploads an image or enters a text query
2. System analyzes input to determine intent and extract features
3. Initial results are displayed based on backbone search
4. User refines search with additional text queries
5. System processes new input in context of previous search
6. Results are refined based on the combined context
7. When satisfied, user proceeds to automatic checkout
8. System verifies purchase details based on confidence level

## Practical Applications

- E-commerce product search and discovery
- Visual shopping assistants
- Automated shopping agents
- Personal shopping recommendations
- Streamlined checkout processes

This architecture provides a complete end-to-end solution for AI-driven shopping experiences, from initial product search to final purchase confirmation. 
