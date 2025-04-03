from ecdsa import SigningKey, VerifyingKey, NIST256p
import hashlib

def init_user():
    private_key = SigningKey.generate(curve=NIST256p)
    public_key = private_key.verifying_key
    return private_key, public_key

def generate_pid(public_key):
    return hashlib.sha256(public_key.to_string()).hexdigest()

def ci_initiate_handshake(ci_private_key, cj_public_key):
    ai = SigningKey.generate(curve=NIST256p)
    Ai = ai.verifying_key
    session_key_ci = ai.privkey.secret_multiplier * cj_public_key.pubkey.point
    shared_key_ci = hashlib.sha256(bytes(str(session_key_ci), 'utf-8')).hexdigest()
    return Ai, shared_key_ci

def cj_respond_handshake(cj_private_key, ci_public_key):
    aj = SigningKey.generate(curve=NIST256p)
    Aj = aj.verifying_key
    session_key_cj = aj.privkey.secret_multiplier * ci_public_key.pubkey.point
    shared_key_cj = hashlib.sha256(bytes(str(session_key_cj), 'utf-8')).hexdigest()
    return Aj, shared_key_cj