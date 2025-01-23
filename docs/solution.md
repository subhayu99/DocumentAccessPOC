# **Document Sharing Solution**

## **Problem Statement**

The challenge was to build an internal application where users could upload documents and control who can access them. The main complexity was ensuring that access could be finely controlled based on Teams (e.g., DevOps, Finance, HR), Projects (e.g., p1, p2), and Organization Levels (e.g., CEO, CTO, Cashier). Furthermore, developers and DevOps had access to everything, potentially undermining the confidentiality of sensitive documents. The solution needed to ensure that users had granular control over who could view, edit, and share documents while maintaining security, especially when some internal users had high-level access.

---

## **Alternative Strategies**

Several alternative strategies could have been employed to solve this problem, including:

1. **Basic Role-Based Access Control (RBAC):**
   - In this approach, access to documents could have been based solely on the roles assigned to users (e.g., admin, user, manager). While simple, this would lack the granularity needed for teams, projects, and organization levels, and it would still not prevent developers or DevOps from having access to everything.

2. **File System Permissions:**
   - Another approach could have been enforcing file-level permissions, where each document’s access rights are handled by the operating system or storage backend. However, this would make it harder to manage and scale as the number of users and documents grows, and it could be error-prone when trying to map document access to specific teams or roles.

3. **Access Control Lists (ACLs):**
   - ACLs allow specific permissions (read, write, delete) to be associated with each document and user. While this is an option, it would require frequent updates as the system evolves, and scaling it would be difficult in a dynamic, team-based structure.

4. **Encryption-Based Access Control:**
   - This approach would involve encrypting documents and using keys to control access. While this could prevent unauthorized access, managing encryption keys and sharing them with the correct users is complex and requires careful handling to avoid compromising security.

---

## **Chosen Implementation & Why It's Better**

The solution adopted is a combination of **encryption-based access control** with a **SharedKeyRegistry**, **token-based authentication (JWT)**, and **public key cryptography**. Here's why this approach stands out:

1. **Granular Control Through SharedKeyRegistry:**
   - The core of this solution is the **SharedKeyRegistry**, a centralized database that tracks which users have access to which documents. This allows for fine-grained control, based on Teams, Projects, and Organization Levels. Unlike RBAC or ACLs, the SharedKeyRegistry is flexible and allows easy modification of access rights for any given document, making it scalable as new teams, projects, or roles are added.

2. **Secure Document Encryption Using AES & RSA:**
   - Documents are encrypted using a **Document Encryption Key (DEK)**, which is encrypted using the recipient’s public RSA key. This ensures that only authorized users (those with the corresponding private key) can decrypt and access the document. This method provides **high security** without requiring users to have direct access to sensitive encryption keys.

3. **JWT for Authentication and Stateless Authorization:**
   - **JWT tokens** are used for authentication, ensuring that only users with valid tokens can interact with the system. This eliminates the need for session management on the server and scales easily. The tokens are passed along with each request, and the system verifies the JWT for every protected API call, ensuring that no unauthorized access is granted.

4. **Passphrase-Protected Private Keys:**
   - By protecting the user’s private key with a passphrase, an extra layer of security is added. Even if an attacker gains access to the private key, they would still need the passphrase to decrypt it. This reduces the risk of key exposure.

5. **Ownership and Access Revocation:**
   - The solution includes mechanisms for **document sharing**, **revocation**, and **deletion**. Owners of the document can add or remove access for specific users at any time, making it highly flexible. Revocation ensures that if a user should no longer have access (e.g., an employee leaves the company), they are immediately denied access to all documents they were previously authorized to access.

6. **Scalability and Flexibility:**
   - The architecture is designed to scale as the number of users, documents, and teams grows. JWT tokens make authentication lightweight and scalable, while the SharedKeyRegistry allows for easy modification of document access rights without having to update complex permissions for each user or document. As the organization evolves, this structure can handle changes in team memberships, project assignments, and organizational roles effortlessly.

---

## **Summary of Benefits**

- **Security**: Document content is encrypted, and access is controlled using public key cryptography and secure tokens, ensuring that unauthorized users cannot view the documents.
- **Granular Access Control**: The SharedKeyRegistry allows for precise control over who can access each document, based on teams, projects, and organizational levels.
- **Scalability**: The use of JWT tokens and the SharedKeyRegistry enables the system to scale without sacrificing performance.
- **User Control**: Document owners can add or revoke access at any time, and sensitive documents are automatically protected using encryption.

This implementation is far more flexible, scalable, and secure than basic RBAC, ACLs, or file system permissions, and it avoids the risks of overly broad access permissions while providing the necessary functionality to manage document access effectively across different teams and projects.

## **Flow Diagram**

Here you can find the API flow diagram (with brief overview): [API Flow](./flow.md)
