# coding: utf-8
# Copyright (c) 2016, 2020, Oracle and/or its affiliates.  All rights reserved.
# This software is dual-licensed to you under the Universal Permissive License (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl or Apache License 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose either license.

from __future__ import absolute_import

import base64
import hashlib
import io
import os
import time
import requests
import httpsig_cffi

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

SIGNATURE_VERSION = "1"

def load_private_key_from_file(filename, pass_phrase=None):
    filename = os.path.expanduser(filename)
    with io.open(filename, mode="rb") as f:
        private_key_data = f.read().strip()
    return load_private_key(private_key_data, pass_phrase)


def load_private_key(secret, pass_phrase):
    if isinstance(secret, unicode):
        secret = secret.encode("ascii")
    if isinstance(pass_phrase, unicode):
        pass_phrase = pass_phrase.encode("ascii")

    backend = default_backend()
    return serialization.load_pem_private_key(secret, pass_phrase, backend=backend)


def inject_missing_headers(request, sign_body):
    # Inject date, host, and content-type if missing
    now = time.gmtime(time.time()) # E.g. Fri, 09 Nov 2001 01:08:47 GMT
    datestr = '%s, %02d %s %04d %02d:%02d:%02d %s' % (['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][now[6]], 
        now[2], ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
         'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][now[1] - 1], now[0], now[3], now[4], now[5],'GMT')
    request.headers.setdefault("date", datestr)
    request.headers.setdefault("host", request.url.split('/')[2])
    request.headers.setdefault("content-type", "application/json")

    # Requests with a body need to send content-type, content-length, and x-content-sha256
    if sign_body:
        # TODO: does not handle streaming bodies (files, stdin)
        body = request.body or ""
        if isinstance(body, basestring):
            body = body.encode("utf-8")
        if "x-content-sha256" not in request.headers:
            m = hashlib.sha256(body)
            base64digest = base64.b64encode(m.digest())
            base64string = base64digest.decode("utf-8")
            request.headers["x-content-sha256"] = base64string
        request.headers.setdefault("content-length", str(len(body)))


# HeaderSigner doesn't support private keys with passwords.
# Patched since the constructor parses the key in __init__
class _PatchedHeaderSigner(httpsig_cffi.sign.HeaderSigner):
    HEADER_SIGNER_TEMPLATE = 'Signature algorithm="rsa-sha256",headers="{}",keyId="{}",signature="%s",version="{}"'

    def __init__(self, key_id, private_key, headers):
        self.sign_algorithm = "rsa"
        self.hash_algorithm = "sha256"

        self._hash = None
        self._rsahash = httpsig_cffi.utils.HASHES[self.hash_algorithm]

        self._rsa_private = private_key
        self._rsa_public = self._rsa_private.public_key()

        self.headers = headers
        self.signature_template = self.HEADER_SIGNER_TEMPLATE.format(" ".join(headers), key_id, SIGNATURE_VERSION)

    def reset_signer(self, key_id, private_key):
        self._hash = None
        self._rsa_private = private_key
        self._rsa_public = self._rsa_private.public_key()
        self.signature_template = self.HEADER_SIGNER_TEMPLATE.format(" ".join(self.headers), key_id, SIGNATURE_VERSION)


class Signer(requests.auth.AuthBase):
    def __init__(self, tenancy, user, fingerprint, private_key_file_location, pass_phrase=None, private_key_content=None):
        self.api_key = tenancy + "/" + user + "/" + fingerprint

        if private_key_content:
            self.private_key = load_private_key(private_key_content, pass_phrase)
        else:
            self.private_key = load_private_key_from_file(private_key_file_location, pass_phrase)

        generic_headers = ["date", "(request-target)", "host"]
        body_headers = ["content-length", "content-type", "x-content-sha256"]
        self.create_signers(self.api_key, self.private_key, generic_headers, body_headers)

    def create_signers(self, api_key, private_key, generic_headers, body_headers):
        self._basic_signer = _PatchedHeaderSigner(
            key_id=api_key,
            private_key=private_key,
            headers=generic_headers)

        self._body_signer = _PatchedHeaderSigner(
            key_id=api_key,
            private_key=private_key,
            headers=generic_headers + body_headers)

    def do_request_sign(self, request):
       # print ('------ before signing:\n')
       # print (request.headers)

        verb = request.method.lower()
        sign_body = verb in ["put", "post", "patch"]
        if sign_body:
            signer = self._body_signer
        else:
            signer = self._basic_signer
            request.headers.pop('Transfer-Encoding', None)

        inject_missing_headers(request, sign_body)
        signed_headers = signer.sign(
            request.headers,
            host=request.url.split('/')[2],
            method=request.method,
            path=request.path_url)

        request.headers.update(signed_headers)
       # print ('------ after signing:\n')
       # print (request.headers)

        return request

    def __call__(self, request):
        return self.do_request_sign(request)