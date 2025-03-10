# Secure Document Management System

A proof-of-concept implementation of a secure document management system that enables granular access control and encrypted document sharing within an organization. This PoC demonstrates the architecture and security mechanisms for protecting sensitive documents while allowing selective sharing based on organizational structure.

## Core Features

- **End-to-End Encryption**: Documents are encrypted using AES & RSA cryptography
- **Granular Access Control**: Share documents based on:
  - Teams (DevOps, Finance, HR)
  - Projects (P1, P2, P3)
  - Organization Levels (CEO, CTO, Managers, etc.)
- **Secure Document Operations**:
  - Upload with automatic encryption
  - Selective sharing with specific users
  - Access revocation
  - Secure document deletion
- **Enhanced Security**: Even system administrators cannot access document contents without proper authorization

## Architecture

The system uses a combination of:
- **SharedKeyRegistry**: Centralized database tracking user access permissions
- **JWT Authentication**: Secure, stateless authorization
- **Public Key Cryptography**: RSA encryption for secure key exchange
- **Document Encryption Keys (DEK)**: AES encryption for document content

## Tech Stack

- FastAPI (Python web framework)
- SQLModel (SQL database ORM)
- Pycryptodome & Cryptography (encryption)
- Python-Multipart (file handling)
- Boto3 (AWS integration)

## Prerequisites

- Python 3.8+
- SQL Database (PostgreSQL recommended)
- AWS credentials (for cloud storage)

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd DocumentAccessPOC
   ```

2. **Set up the environment**
   ```bash
   # Create and activate virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   # Install dependencies
   pip install -r requirements.txt
   ```

## Configuration

1. Configure your database connection in `config.py`
2. Set up AWS credentials if using cloud storage
3. Configure JWT secret key and other security parameters

## API Usage

### Authentication
```bash
# Create a new user
curl -X POST "http://localhost:8000/users" \
     -H "Content-Type: application/json" \
     -d '{"username": "user1", "password": "secure_password"}'

# Get authentication token
curl -X POST "http://localhost:8000/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=user1&password=secure_password"
```

### Document Operations
```bash
# Upload a document
curl -X POST "http://localhost:8000/documents" \
     -H "Authorization: Bearer <token>" \
     -F "file=@document.pdf" \
     -F "share_with=user2,user3"

# Share a document
curl -X PUT "http://localhost:8000/documents/{doc_id}/share" \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"share_with": ["user4", "user5"]}'

# Download a document
curl -X GET "http://localhost:8000/documents/{doc_id}" \
     -H "Authorization: Bearer <token>" \
     --output downloaded_document.pdf
```

## API Endpoints

- **Authentication**
  - POST `/token`: Login and get access token

- **Users**
  - POST `/users`: Create new user
  - GET `/users/me`: Get current user profile
  - GET `/users`: Get user profiles by IDs

- **Documents**
  - POST `/documents`: Upload document
  - GET `/documents/{doc_id}`: Download document
  - PUT `/documents/{doc_id}/share`: Share document
  - PUT `/documents/{doc_id}/revoke`: Revoke access
  - DELETE `/documents/{doc_id}`: Delete document
  - GET `/documents`: List accessible documents

## System Flow

### User Management
1. **User Creation**
   - System generates passphrase and RSA key pair
   - Private key is encrypted using AES-GCM with passphrase
   - Public key and encrypted private key stored in database

2. **Authentication Flow**
   - User provides userid and passphrase
   - System verifies credentials and generates JWT token
   - Token used for subsequent API requests

### Document Operations Flow

1. **Document Upload**
   - System verifies JWT token and user passphrase
   - Generates unique Document ID based on content hash
   - Creates Document Encryption Key (DEK) for new documents
   - Encrypts document with DEK and stores in backend
   - Updates SharedKeyRegistry with access permissions

2. **Document Sharing**
   - Owner initiates sharing with specific users
   - System encrypts DEK with recipients' public keys
   - Updates SharedKeyRegistry with new access entries

3. **Document Retrieval**
   - System verifies user's JWT token
   - Decrypts user's private key using passphrase
   - Checks SharedKeyRegistry for access permissions
   - Retrieves and decrypts document using DEK

4. **Access Control**
   - Document owners can revoke access
   - System removes entries from SharedKeyRegistry
   - Automatic cleanup of related encryption keys

## Implementation Details

### Security Implementation

1. **Key Management**
   ```
   User Keys:
   - RSA key pair per user
   - Private key encrypted with AES-GCM
   - Public key stored in plain text
   
   Document Keys:
   - Unique DEK per document
   - DEK encrypted with recipient public keys
   - Stored in SharedKeyRegistry
   ```

2. **Access Control Matrix**
   ```
   Permissions:
   - Owner: Full control (read, share, revoke, delete)
   - Shared User: Read access
   - Team/Project Based: Configurable access levels
   ```

3. **Storage Security**
   ```
   - Documents encrypted at rest
   - Metadata stored separately
   - Access logs for audit trails
   ```

### Database Schema

```sql
Users:
- id: UUID
- username: String
- public_key: String
- encrypted_private_key: String

Documents:
- id: UUID
- owner_id: UUID (foreign key)
- encrypted_content: Bytes
- metadata: JSON

SharedKeyRegistry:
- document_id: UUID
- user_id: UUID
- encrypted_dek: String
```

## Security Features

1. **Document Encryption**
   - Each document is encrypted with a unique Document Encryption Key (DEK)
   - DEK is encrypted with recipient's public RSA key
   - Only authorized users can decrypt and access documents

2. **Access Control**
   - Fine-grained control through SharedKeyRegistry
   - Dynamic sharing and revocation
   - No document duplication required for sharing

3. **Authentication**
   - JWT-based authentication
   - Passphrase-protected private keys
   - Secure token management

## Documentation

Additional documentation can be found in the `docs` directory:
- [Solution Architecture](docs/solution.md)
- [API Flow](docs/flow.md)
- [Extensibility Guide](docs/extensibility.md)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
