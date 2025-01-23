# API Flow

## Flow Diagram

```mermaid
---
config:
  look: classic # handDrawn
  layout: elk # dagre
  theme: dark
---
flowchart TD
    %% User Node
    U["User"]

    %% User Creation
    subgraph User_Creation
        UC1["POST /users (user details, ID)"] --> UC2["Generate passphrase & RSA key pair (private and public key)"]
        UC2 --> UC3["Encrypt the private key with passphrase using AES-GCM"]
        UC3 --> UC4["Save user details, public key, encrypted private key in Database"]
        UC4 --> UC5["Return the User details along with passphrase"]
    end

    %% Token Generation
    subgraph Token_Generation
        TG1["POST /token (userid, passphrase)"] --> TG2["Verify user and passphrase"]
        TG2 --> TG3["Generate JWT token"]
        TG3 --> TG4["Return JWT token"]
    end

    %% Document Upload
    subgraph Document_Upload
        DU1["POST /documents (file, passphrase, user IDs, token)"] --> DU2["Verify JWT token"]
        DU2 --> DU3["Verify user with passphrase"]
        DU3 --> DU4["Generate the Document ID using the file content hash + user ID + filename"]
        DU4 --> DU5["Check if document exists in Database"]
        DU5 -->|Exists| DU6["Update SharedKeyRegistry with new user IDs"]
        DU5 -->|Doesn't Exist| DU7["Generate DEK (random AES key)"]
        DU7 --> DU8["Encrypt file content and upload to Storage Backend"]
        DU8 --> DU9["Save Document object in Database"]
        DU9 --> DU6
        DU6 --> DU10["Save SharedKeyRegistry entries"]
        DU10 --> DU11["Return the Document object"]
    end

    %% Document Sharing
    subgraph Document_Sharing
        DS1["PUT /documents/{doc_id}/share (passphrase, user IDs, token)"] --> DS2["Verify JWT token"]
        DS2 --> DS3["Verify ownership"]
        DS3 -->|Owner Verified| DS4["Encrypt DEK with new users' public keys"]
        DS4 --> DS5["Update SharedKeyRegistry with new entries"]
        DS3 -->|Unauthorized| DS6["Error: Unauthorized"]
    end

    %% Document Retrieval
    subgraph Document_Retrieval
        DR1["GET /documents/{doc_id} (passphrase, token)"] --> DR2["Verify JWT token"]
        DR2 --> DR3["Fetch user's encrypted private key"]
        DR3 --> DR4["Decrypt private key using passphrase"]
        DR4 --> DR5["Check SharedKeyRegistry for user_id and doc_id"]
        DR5 -->|Entry Found| DR6["Decrypt shared key (DEK) using private key"]
        DR6 --> DR7["Fetch encrypted document from Storage Backend"]
        DR7 --> DR8["Decrypt document using DEK"]
        DR8 --> DR9["Return decrypted file content"]
        DR5 -->|Entry Not Found| DR10["Error: Access Denied"]
    end

    %% Access Revocation
    subgraph Access_Revocation
        AR1["PUT /documents/{doc_id}/revoke (passphrase, user IDs, token)"] --> AR2["Verify JWT token"]
        AR2 --> AR3["Verify ownership"]
        AR3 -->|Owner Verified| AR4["Remove user IDs from SharedKeyRegistry"]
        AR3 -->|Unauthorized| AR5["Error: Unauthorized"]
    end

    %% Document Deletion
    subgraph Document_Deletion
        DD1["DELETE /documents/{doc_id} (passphrase, token)"] --> DD2["Verify JWT token"]
        DD2 --> DD3["Verify ownership"]
        DD3 -->|Owner Verified| DD4["Remove Document object from Database"]
        DD4 --> DD5["Remove entries from SharedKeyRegistry"]
        DD5 --> DD6["Delete file from Storage Backend"]
        DD3 -->|Unauthorized| DD7["Error: Unauthorized"]
    end

    %% Connections to User
    U --> UC1 & TG1
    TG4 --> DU1
    TG4 --> DS1
    TG4 --> DR1
    TG4 --> AR1
    TG4 --> DD1
```

---

## **Flow Overview:**

This flow diagram represents the interactions within the Document Management and Sharing API, including user creation, document upload, sharing, retrieval, access revocation, deletion, and token-based authentication.

1. **User Creation:**
   - A user is created via the `POST /users` route, where their basic details and ID are submitted.
   - The system generates a passphrase, RSA key pair, and encrypts the private key using AES-GCM.
   - The public key, encrypted private key, and other user details are saved in the database, and the user receives the necessary information, including the passphrase.

2. **Token Generation:**
   - The `POST /token` endpoint is used to authenticate the user by verifying their `userid` and `passphrase`.
   - If valid, a **JWT token** is generated and returned, which will be used in future requests for authentication.

3. **Document Upload:**
   - A user can upload a document using the `POST /documents` endpoint, where the document file, passphrase, and IDs of users with whom the document should be shared are provided.
   - The system verifies the JWT token, checks the user’s passphrase, and generates a Document ID based on the file content.
   - If the document already exists, it updates the sharing registry; otherwise, a new document is created, encrypted with a unique Document Encryption Key (DEK), and stored.
   - The DEK is then encrypted with the public keys of the users to share the document securely.

4. **Document Sharing:**
   - The `PUT /documents/{doc_id}/share` endpoint allows the owner of a document to share it with additional users.
   - The system verifies the JWT token and ownership before encrypting the DEK with the public keys of the new users and updating the SharedKeyRegistry.

5. **Document Retrieval:**
   - Users can retrieve documents via the `GET /documents/{doc_id}` endpoint by providing their passphrase and JWT token.
   - The system verifies the user’s token, decrypts their private key using the passphrase, and checks the SharedKeyRegistry for the document's access.
   - If access is granted, the encrypted document is fetched from the storage backend, decrypted using the DEK, and returned.

6. **Access Revocation:**
   - The owner can revoke access to a document using the `PUT /documents/{doc_id}/revoke` endpoint.
   - The system verifies the owner’s JWT token and removes the revoked user IDs from the SharedKeyRegistry.

7. **Document Deletion:**
   - The owner can delete a document using the `DELETE /documents/{doc_id}` endpoint.
   - The system verifies ownership and removes the document from the database, deletes entries from the SharedKeyRegistry, and removes the document from the storage backend.
