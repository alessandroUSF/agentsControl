# Signing key of the registrations

The registration commits and their tags are signed by the PI with an SSH key (Section 14.1 of the protocol).

- Public key: `agentscontrol_signing.pub` (ED25519, comment "agentsControl signing key").
- Fingerprint: `SHA256:d/V3o3olciAxvIl18rYcUrWQhm/PURLjQ9f7OH/4Asw`.
- Created by the PI on 13 November 2026. The private key never leaves the PI's computer and is protected by a passphrase.

To check a registration tag and its commit:

```bash
git -c gpg.ssh.allowedSignersFile=docs/signing/allowed_signers verify-tag <tag>
git -c gpg.ssh.allowedSignersFile=docs/signing/allowed_signers verify-commit <tag>^{commit}
```
