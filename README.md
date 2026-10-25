# SHL Assessment Recommendation Agent

An AI-powered assessment recommendation system that helps recruiters identify relevant SHL assessments based on job roles, technical skills, seniority, and hiring requirements. The application combines semantic search, metadata filtering, rule-based ranking, and conversational context management to generate relevant assessment recommendations.

**Live Application:** [Try the SHL Assessment Recommendation Agent](https://cmjadhav-shl-assessment-agent.hf.space)

**Interactive API Documentation:** [Explore the API with Swagger UI](https://cmjadhav-shl-assessment-agent.hf.space/docs)

---

## Table of Contents

- [Project Overview](#project-overview)
- [Problem Statement](#problem-statement)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [System Architecture](#system-architecture)
- [How It Works](#how-it-works)
- [Conversational Capabilities](#conversational-capabilities)
- [API Endpoints](#api-endpoints)
- [Example API Requests](#example-api-requests)
- [Example Response](#example-response)
- [Evaluation and Improvements](#evaluation-and-improvements)
- [Deployment](#deployment)
- [Project Structure](#project-structure)
- [Local Setup](#local-setup)
- [Future Enhancements](#future-enhancements)
- [Author](#author)

---

## Project Overview

Recruiters often need to identify appropriate assessments for different job roles while considering technical competencies, experience levels, job requirements, and organizational preferences.

The SHL Assessment Recommendation Agent addresses this challenge through an intelligent retrieval and recommendation pipeline.

The application processes natural-language queries and job descriptions, identifies relevant hiring requirements, searches an SHL assessment catalog, filters incompatible results, and ranks the remaining assessments based on contextual relevance.

It also supports multi-turn conversations, allowing users to refine recommendations, provide additional requirements, and compare assessments without restarting the interaction.

The application is implemented as a FastAPI service and deployed using Docker on Hugging Face Spaces.

## Problem Statement

Traditional assessment selection can require recruiters to manually explore large product catalogs and compare assessments against job requirements.

This project aims to simplify the process by developing an AI-powered system that can:

- Understand assessment requirements expressed in natural language.
- Retrieve assessments relevant to a particular job role and skill set.
- Filter and rank results according to available catalog information.
- Maintain conversational context across multiple requests.
- Refine recommendations when users introduce new constraints.
- Compare assessments using available catalog metadata.
- Provide assessment names and direct catalog URLs.

## Key Features

### 1. Semantic Search

Uses Sentence Transformers to convert assessment catalog entries and user queries into vector embeddings. FAISS performs similarity-based retrieval to identify potentially relevant assessments.

### 2. Context-Aware Recommendations

Extracts relevant information from user conversations, including:

- Job role
- Seniority level
- Required skills
- Domain requirements
- Remote-work preferences
- Adaptive assessment preferences
- Requested products
- Excluded products
- Assessment comparison requests

### 3. Metadata Filtering

Filters retrieved assessments according to applicable catalog metadata and user constraints, such as remote or adaptive assessment requirements.

### 4. Rule-Based Ranking

Reranks candidate assessments using factors such as role relevance, skill overlap, seniority, domain relevance, product requests, and query overlap.

### 5. Multi-Turn Conversation

Preserves conversation history and merges new requirements with previously established context.

For example, a recruiter can request assessments for a Java developer and subsequently ask to include personality assessments.

### 6. Assessment Comparison

Supports requests to compare assessments, using information available in the assessment catalog rather than relying solely on the language model's prior knowledge.

### 7. Input Guardrails

Includes checks intended to identify prompt-injection attempts and reject off-topic queries before retrieval.

### 8. REST API

Exposes the application through FastAPI endpoints and provides automatically generated interactive documentation.

### 9. Docker-Based Deployment

Containerizes the application for deployment on Hugging Face Spaces.

---

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| FastAPI | REST API development |
| Sentence Transformers | Text embedding generation |
| all-MiniLM-L6-v2 | Sentence embedding model |
| FAISS | Vector similarity search |
| NumPy | Numerical operations and vector processing |
| Pydantic | API request and response validation, where configured |
| Docker | Application containerization |
| Hugging Face Spaces | Application hosting and deployment |
| Git and GitHub | Version control and project documentation |

*The table describes the documented technology stack. Retain individual libraries in the final version only if they are present in your implementation.*

---

## System Architecture

The application follows a modular architecture that separates conversation processing, retrieval, filtering, ranking, and response generation.

```text
                 User Query / Job Description
                            |
                            v
                   FastAPI Chat Endpoint
                            |
                            v
                   Input Guardrails
             Prompt-Injection and Topic Checks
                            |
                            v
                  Conversation State
                      Extraction
                            |
                            v
                  Query Representation
                            |
                            v
                Semantic Retrieval Layer
                Sentence Transformers
                            |
                            v
                    FAISS Vector Search
                            |
                            v
                    Metadata Filtering
                            |
                            v
                    Ranking Module
                            |
                            v
                 Recommendation / Comparison
                            |
                            v
                   Structured API Response
                            |
                            v
                           User
```

### Core Components

**1. State Extractor**

Processes conversation history and extracts structured hiring requirements. This information helps the system interpret follow-up requests and retain relevant context.

**2. Guardrails**

Checks incoming requests for prompt-injection attempts and off-topic content before proceeding to retrieval.

**3. Retriever**

Generates or uses text embeddings and performs semantic search against the SHL assessment catalog using FAISS.

**4. Metadata Filter**

Removes assessments that do not satisfy applicable requirements represented in the catalog metadata.

**5. Ranking Module**

Improves the ordering of retrieved assessments using hiring context, including role, skills, seniority, domain, and query relevance.

**6. Comparison Module**

Processes comparison requests using available assessment catalog information.

This modular design supports debugging, testing, and future extension of individual components.

---

## How It Works

The recommendation pipeline consists of three primary retrieval stages.

### Stage 1: Semantic Retrieval

Assessment catalog entries are represented using embeddings generated with the `all-MiniLM-L6-v2` Sentence Transformers model.

FAISS uses an `IndexFlatIP` index to retrieve candidates through inner-product similarity search.

The quality of similarity ranking depends on the embedding representation and the vector normalization strategy used by the implementation.

### Stage 2: Metadata Filtering

Retrieved candidates are checked against applicable requirements, including assessment preferences and other available catalog constraints.

Assessments that do not satisfy relevant constraints are removed.

### Stage 3: Rule-Based Reranking

The remaining candidates are reranked using contextual signals, such as:

- Job role relevance
- Required technical skills
- Seniority requirements
- Domain overlap
- Requested assessment products
- Query-term overlap

The system returns between one and ten recommendations, depending on the retrieval and filtering results.

Each recommendation includes:

- Assessment name
- SHL catalog URL
- Test type

---

## Conversational Capabilities

The agent supports four primary conversational behaviors.

### 1. Clarification

When a request does not contain enough information to identify suitable assessments, the system can ask for additional hiring requirements.

Example:

**User:**
```text
Recommend assessments for a software developer.
```

The system can use the available context and clarification logic to determine whether additional information is needed.

### 2. Recommendation

When sufficient context is available, the agent retrieves and ranks relevant assessments.

Example:

**User:**
```text
Recommend assessments for a Java developer.
```

The system searches the catalog for assessments related to Java and returns a ranked list of candidates with their catalog URLs.

### 3. Refinement

The agent preserves conversation history so that new requirements can update the existing request.

Example conversation:

**User:**
```text
Recommend assessments for a Java developer.
```

**User follow-up:**
```text
Actually, add personality tests.
```

The application merges the additional requirement with the existing hiring context instead of treating the follow-up as an entirely unrelated request.

### 4. Comparison

The agent supports requests to compare two SHL assessments using available catalog data.

Example:

```text
What is the difference between OPQ and GSA?
```

The comparison functionality is intended to use assessment metadata rather than relying exclusively on the language model's pretrained knowledge.

The actual quality of a comparison depends on whether the relevant information is available in the catalog.

---

## API Endpoints

The application exposes the following endpoints.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Returns service information and API links |
| GET | `/health` | Checks whether the service is running |
| POST | `/chat` | Processes conversations and returns recommendations or comparison responses |
| GET | `/docs` | Provides interactive Swagger API documentation |

### Base URL

```text
https://cmjadhav-shl-assessment-agent.hf.space
```

### Interactive Documentation

```text
https://cmjadhav-shl-assessment-agent.hf.space/docs
```

---

## Example API Requests

### Example 1: Recommend Assessments for a Java Developer

**Endpoint:**

```http
POST /chat
Content-Type: application/json
```

**Request:**

```json
{
  "messages": [
    {
      "role": "user",
      "content": "Recommend assessments for a Java developer."
    }
  ]
}
```

**Expected response structure:**

```json
{
  "reply": "I found relevant SHL assessments for your Java requirements.",
  "recommendations": [
    {
      "name": "Java 2 Platform Enterprise Edition 1.4 Fundamental",
      "url": "https://www.shl.com/products/product-catalog/view/java-2-platform-enterprise-edition-1-4-fundamental/",
      "test_type": "U"
    }
  ],
  "end_of_conversation": false
}
```

The example illustrates the response structure. The actual recommendations and number of returned results depend on the deployed catalog and retrieval pipeline.

### Example 2: Refine Existing Recommendations

**Request:**

```json
{
  "messages": [
    {
      "role": "user",
      "content": "Recommend assessments for a Java developer."
    },
    {
      "role": "assistant",
      "content": "Here are relevant assessments for a Java developer."
    },
    {
      "role": "user",
      "content": "Actually, add personality tests."
    }
  ]
}
```

The application uses the supplied conversation history to interpret the new requirement in the context of the existing request.

**Expected behavior:**

- Preserve the Java developer requirement.
- Incorporate the additional personality-assessment requirement.
- Retrieve and rank relevant candidates.
- Return the updated recommendation response.

### Example 3: Recommend Assessments from a Job Description

**Request:**

```json
{
  "messages": [
    {
      "role": "user",
      "content": "Here is the job description: We are hiring a Java developer with Spring Boot experience. The candidate must communicate with clients. This is a remote role."
    }
  ]
}
```

The system extracts relevant information from the job description and uses it to guide retrieval and ranking.

Relevant information includes:

- Job role: Java developer
- Technical skills: Java and Spring Boot
- Communication requirement: Client communication
- Work preference: Remote

The final recommendations depend on the information represented in the catalog and the application's implemented ranking logic.

---

## Evaluation and Improvements

The application was evaluated using assignment sample conversations and additional custom test cases.

Evaluation focused on the following areas.

### Retrieval Quality

Examined whether relevant assessments appeared among the retrieved candidates.

### Recommendation Relevance

Reviewed whether the returned assessments aligned with the user's role, skills, and stated requirements.

### Groundedness

Considered whether recommendation and comparison responses were supported by available catalog information.

### Conversation Correctness

Tested clarification, recommendation, refinement, and comparison scenarios involving conversational context.

### Prompt-Injection and Off-Topic Robustness

Evaluated the application's input checks against prompt-injection attempts and unrelated requests.

### Improvements Implemented

Several iterations were performed to improve the system:

- Enhanced role and skill extraction.
- Improved conversation-state merging across turns.
- Refined assessment ranking.
- Added alias matching for assessment names such as OPQ, MQ, and GSA.
- Strengthened prompt-injection and off-topic detection.

These improvements were intended to make recommendations more context-aware and improve the reliability of conversational interactions.

---

## Deployment

The application is containerized using Docker and deployed on Hugging Face Spaces.

**Live Application:** [SHL Assessment Recommendation Agent](https://cmjadhav-shl-assessment-agent.hf.space)

**API Documentation:** [Swagger UI](https://cmjadhav-shl-assessment-agent.hf.space/docs)

**Chat API:** [POST /chat](https://cmjadhav-shl-assessment-agent.hf.space/chat)

The application URL is the primary entry point. Reviewers can access the interactive API documentation through the `/docs` route.

### Environment Variables

Any API credentials or other secrets required by the implementation should be configured through environment variables or the deployment platform's secret-management settings.

**Never commit access tokens, API keys, passwords, or other credentials to the repository.**

---

## Project Structure

The exact file structure depends on the repository. A possible organization for this modular application is:

```text
shl-assessment-recommendation-agent/
│
├── app/
│   ├── main.py
│   ├── state_extractor.py
│   ├── guardrails.py
│   ├── retriever.py
│   ├── ranking.py
│   └── comparison.py
│
├── data/
│   └── assessment_catalog
│
├── tests/
│   └── test_cases.py
│
├── Dockerfile
├── requirements.txt
├── README.md
└── .gitignore
```

This is an illustrative structure, not a verified listing of the actual repository files. Update it to match your implementation before publishing.

---

## Local Setup

The following steps describe a typical setup for a Python and FastAPI application. The exact commands and configuration may need to be adjusted to match your repository.

### Prerequisites

- Python
- Git
- pip
- Docker, if you want to run the containerized application

### 1. Clone the Repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd <YOUR_REPOSITORY_DIRECTORY>
```

Replace the placeholders with your actual GitHub repository URL and directory name.

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate the environment.

**Windows:**

```bash
.venv\Scripts\activate
```

**Linux or macOS:**

```bash
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Ensure the dependency file includes the packages required by your actual implementation.

### 4. Configure Environment Variables

Set any required credentials using environment variables. Do not place secrets directly in source code or commit them to Git.

### 5. Start the Application

If `app
