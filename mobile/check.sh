#!/bin/sh
set -eu
cd "$(dirname "$0")"
mobile_check_dir=$(mktemp -d "${TMPDIR:-/tmp}/zigzag-phone-check.XXXXXX")
trap 'rm -rf "$mobile_check_dir"' EXIT HUP INT TERM
swiftc -swift-version 5 -module-cache-path "$mobile_check_dir/cache" -typecheck Core.swift DriveTransport.swift
swiftc -swift-version 5 -module-cache-path "$mobile_check_dir/cache" Core.swift DriveTransport.swift CoreTests.swift -o "$mobile_check_dir/tests"
"$mobile_check_dir/tests"
# Syntax only: iOS type checking/build requires Xcode and the iPhone SDK.
swiftc -frontend -parse -target arm64-apple-ios17.0 PhoneApp.swift
plutil -lint ZigzagPhone.xcodeproj/project.pbxproj
