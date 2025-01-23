# Ease of Extensibility

The chosen approach, combining encryption-based access control with a SharedKeyRegistry, is designed for flexibility and extensibility. Here's how it simplifies scenarios like granting some users edit access while others have read-only access:

---

## 1. Dynamic Role Assignment in the SharedKeyRegistry

### How it Works
The SharedKeyRegistry maps users to documents and specifies their access level (e.g., Read, Edit, Share). For example:

| DocumentID | UserID | AccessLevel |
|------------|--------|-------------|
| Doc123     | UserA  | Read        |
| Doc123     | UserB  | Edit        |
| Doc123     | UserC  | Read        |

### Extensibility
To modify permissions, you simply update the user's `AccessLevel` in the registry. No need to duplicate documents or re-encrypt files for each permission change.

**Example:**  
If UserC needs Edit access, you update their entry to `Edit`. This avoids document duplication or re-encryption.

---

## 2. Granular Access Control

### Read vs. Edit
- **Read Access**: A user's private key allows decryption of the document for viewing.
- **Edit Access**: The system could additionally store a "Write Key" in the registry for users with edit permissions. Only users with Edit access can modify the document, re-encrypt it, and update the registry with the new encryption key.

### Share Access
Users with Share permissions can grant other users access by updating the SharedKeyRegistry (if the owner allows delegation).

---

## 3. Minimal Effort to Scale to New Use Cases

### Adding New Roles
If a new access level (e.g., "Comment") needs to be introduced, it's straightforward to extend the `AccessLevel` enum in the database and update the system's logic to handle the new role.

### Example Scenario
**Add a "Comment" role**:  
Users with this access can decrypt the document but cannot modify it. The system can enforce this by disallowing re-encryption for these users.

### Supporting Multiple Teams/Projects
The registry can easily associate documents with teams or projects, granting shared access without creating duplicate entries.

---

## 4. Key Revocation and Propagation

- **Revoking Edit Access**:  
  When a user loses Edit access, their permissions are updated in the registry. The document owner can optionally rotate the encryption key to ensure past access cannot be exploited (e.g., if the user cached the decryption key).

- **Granting New Access**:  
  Adding a new user with specific permissions simply requires adding an entry in the registry and sharing the Document Encryption Key (DEK) encrypted with their public key.

---

## 5. Built-In Security for Multiple Access Levels

The encryption-based model ensures users can only perform actions permitted by their role:
- **Read Access**: Users can only decrypt the content.
- **Edit Access**: Users can decrypt, modify, and re-encrypt content (if authorized).
- **Owner Access**: The owner has full control to share, revoke, or delete documents.

By enforcing these access levels at the cryptographic level, the system remains secure while allowing flexibility in permission updates.

---

## Benefits of Extensibility

1. **No Document Duplication**:  
   You don’t need multiple copies for different access levels—permissions are tied to the registry and encryption keys.

2. **Scalability**:  
   Adding or removing users and adjusting their permissions is lightweight and doesn’t require document reprocessing.

3. **Granularity**:  
   The model supports fine-grained access control without making the system overly complex.

4. **Future-Proof**:  
   New access roles (e.g., "Comment" or "View History") or more complex team structures can be added without disrupting the existing system.

---

In summary, the design allows seamless addition or modification of access levels while maintaining robust security, avoiding duplication, and ensuring smooth collaboration.