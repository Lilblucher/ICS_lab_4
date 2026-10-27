#!/usr/bin/env bash
# Run this on the Kali partition before capturing traffic for Part A.
#
# What it does: sets SSLKEYLOGFILE so that Chrome/Firefox dump the TLS
# session secrets (the key material needed to decrypt traffic) to a log
# file as they happen. Wireshark can then use that file to decrypt the
# capture after the fact — without this, TLS 1.3 traffic is just
# unreadable ciphertext in Wireshark, by design.
#
# IMPORTANT: this only works if the browser is *launched* from a shell
# that already has this variable exported. Setting it after the browser
# is already open does nothing for that running instance.

set -euo pipefail

LOGFILE="$HOME/sslkeys.log"

echo "export SSLKEYLOGFILE=\"$LOGFILE\"" >> ~/.bashrc
export SSLKEYLOGFILE="$LOGFILE"

echo "SSLKEYLOGFILE set to: $LOGFILE"
echo "Added to ~/.bashrc so it persists across terminal sessions."
echo
echo "Next steps:"
echo "  1. Close ALL open browser windows (Chrome/Firefox) completely."
echo "  2. Open a NEW terminal (so ~/.bashrc is re-read), then launch the"
echo "     browser FROM that terminal, e.g.:  firefox &   or   google-chrome &"
echo "  3. Visit any HTTPS site, then run:  cat \"$LOGFILE\""
echo "     You should see lines starting with CLIENT_RANDOM or similar."
echo "  4. In Wireshark: Edit -> Preferences -> Protocols -> TLS ->"
echo "     '(Pre)-Master-Secret log filename' -> point it at $LOGFILE"
