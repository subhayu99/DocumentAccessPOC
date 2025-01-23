# **Document Sharing Solution**

## **Problem Statement**

The challenge was to build an internal application where users could upload documents and control who can access them. The main complexity was ensuring that access could be finely controlled based on Teams (e.g., DevOps, Finance, HR), Projects (e.g., p1, p2), and Organization Levels (e.g., CEO, CTO, Cashier). Furthermore, developers and DevOps had access to everything, potentially undermining the confidentiality of sensitive documents. The solution needed to ensure that users had granular control over who could view, edit, and share documents while maintaining security, especially when some internal users had high-level access.

---

## **Alternative Strategies**

Several alternative strategies could have been employed to solve this problem, including:

### 1. **Basic Role-Based Access Control (RBAC)**

**How it Works:**  
Users are assigned specific roles (e.g., Admin, Manager, Employee), and each role is granted predefined permissions (e.g., Admin can access all documents, Manager can access department-level documents, Employee can only access their own documents).

**Problems:**  
- **Lack of Granularity:** RBAC doesn’t easily accommodate scenarios where permissions need to vary based on Teams, Projects, or Organization Levels. For example, it’s challenging to limit access to "HR documents related to Project X."  
- **Overly Broad Access:** Roles like Admin or Developer might inherently have access to everything, which undermines confidentiality for sensitive documents.  
- **Difficult to Adapt:** As teams or projects change, or as new organizational levels are added, the roles and their associated permissions need frequent updates, leading to increased maintenance overhead.  

---

### 2. **File System Permissions**

**How it Works:**  
Document access is managed directly by the file system or storage backend, where each file has permissions set for read, write, and execute operations based on users or groups.

**Problems:**  
- **Scalability Issues:** Managing file-level permissions becomes unmanageable as the number of users and documents grows. Every new document or user addition requires manual adjustments.  
- **No Team-Based Logic:** File systems don’t inherently understand organizational structures like Teams or Projects, making it hard to enforce hierarchical or team-specific permissions.  
- **Duplication for Sharing:** Sharing a document often requires duplicating it into a different location with separate permissions, leading to storage inefficiency and version control problems (e.g., conflicting edits or outdated copies).  

---

### 3. **Access Control Lists (ACLs)**

**How it Works:**  
Each document is associated with a list of users and their specific permissions (e.g., User A: Read, User B: Write/Delete).

**Problems:**  
- **Frequent Updates:** In dynamic environments, ACLs require constant updates whenever a team member joins, leaves, or changes roles, which is error-prone.  
- **Complexity in Management:** Managing ACLs for thousands of documents and users becomes unwieldy, especially when users belong to multiple teams or projects.  
- **Duplication for Sharing:** If the same document needs to be shared with different permissions across multiple teams, duplication may again be necessary to handle separate ACLs, creating inefficiencies and inconsistencies.  

---

### 4. **Encryption-Based Access Control**

**How it Works:**  
Documents are encrypted, and access is controlled by sharing encryption keys with authorized users. Public key cryptography (e.g., RSA) is often used to secure the keys.

**Problems:**  
- **Key Management Complexity:** Sharing, storing, and revoking encryption keys is non-trivial. Mistakes in key handling can compromise security or lead to access issues.  
- **Collaboration Challenges:** If multiple users need write access to a document, managing and updating the encryption keys for every change can become cumbersome.  
- **Duplication for Sharing:** To share a document with a different set of users, a new encryption key may need to be generated and the document re-encrypted, leading to potential duplication of encrypted versions.  

---

### **Document Duplication: A Critical Pain Point**

Duplication of documents is a recurring challenge across these alternatives:

1. **Storage Overhead:** If multiple versions of a document exist due to sharing or team-specific modifications, storage usage can balloon unnecessarily.  
2. **Version Control Issues:** Different versions can lead to confusion, especially if changes are made to one version but not propagated to others.  
3. **Security Risk:** If older or duplicate versions aren’t properly deleted, they may become a vulnerability, allowing unauthorized access.  

---

## **Chosen Implementation & Why It's Better**

The solution adopted is a combination of **encryption-based access control** with a **SharedKeyRegistry**, **token-based authentication (JWT)**, and **public key cryptography**. Here's why this approach stands out:

1. **Granular Control Through SharedKeyRegistry:**  
   The core of this solution is the **SharedKeyRegistry**, a centralized database that tracks which users have access to which documents. This allows for fine-grained control, based on Teams, Projects, and Organization Levels. Unlike RBAC or ACLs, the SharedKeyRegistry is flexible and allows easy modification of access rights for any given document, making it scalable as new teams, projects, or roles are added.

2. **Secure Document Encryption Using AES & RSA:**  
   Documents are encrypted using a **Document Encryption Key (DEK)**, which is encrypted using the recipient’s public RSA key. This ensures that only authorized users (those with the corresponding private key) can decrypt and access the document. This method provides **high security** without requiring users to have direct access to sensitive encryption keys.

3. **JWT for Authentication and Stateless Authorization:**  
   **JWT tokens** are used for authentication, ensuring that only users with valid tokens can interact with the system. This eliminates the need for session management on the server and scales easily. The tokens are passed along with each request, and the system verifies the JWT for every protected API call, ensuring that no unauthorized access is granted.

4. **Passphrase-Protected Private Keys:**  
   By protecting the user’s private key with a passphrase, an extra layer of security is added. Even if an attacker gains access to the private key, they would still need the passphrase to decrypt it. This reduces the risk of key exposure.

5. **Ownership and Access Revocation:**  
   The solution includes mechanisms for **document sharing**, **revocation**, and **deletion**. Owners of the document can add or remove access for specific users at any time, making it highly flexible. Revocation ensures that if a user should no longer have access (e.g., an employee leaves the company), they are immediately denied access to all documents they were previously authorized to access.

6. **Avoidance of Duplication:**  
   - **Centralized Access via the SharedKeyRegistry:** A single encrypted document is stored. The SharedKeyRegistry dynamically manages access, removing the need for duplicate copies.  
   - **Dynamic Sharing and Revocation:** Owners can modify access rights without creating new versions of the document.  
   - **Efficient Collaboration:** All users work on the same encrypted document while maintaining security.  

7. **Scalability and Flexibility:**  
   The architecture is designed to scale as the number of users, documents, and teams grows. JWT tokens make authentication lightweight and scalable, while the SharedKeyRegistry allows for easy modification of document access rights without having to update complex permissions for each user or document.  

---

## **Summary of Benefits**

- **Security:** Document content is encrypted, and access is controlled using public key cryptography and secure tokens, ensuring that unauthorized users cannot view the documents.  
- **Granular Access Control:** The SharedKeyRegistry allows for precise control over who can access each document, based on teams, projects, and organizational levels.  
- **Scalability:** The use of JWT tokens and the SharedKeyRegistry enables the system to scale without sacrificing performance.  
- **User Control:** Document owners can add or revoke access at any time, and sensitive documents are automatically protected using encryption.  

This implementation is far more flexible, scalable, and secure than basic RBAC, ACLs, or file system permissions, and it avoids the risks of overly broad access permissions while providing the necessary functionality to manage document access effectively across different teams and projects.

---

## **Flow Diagram**

Here you can find the API flow diagram (with a brief overview): [API Flow](./flow.md)