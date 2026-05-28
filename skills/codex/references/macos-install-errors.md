# macOS Codex Install: Common Errors & Diagostics

## Error: "Missing optional dependency @openai/codex-darwin-x64"

Full trace:
```
Error: Missing optional dependency @openai/codex-darwin-x64. Reinstall Codex: npm install -g @openai/codex@latest
    at file:///.../node_modules/@openai/codex/bin/codex.js:100:11
    at ModuleJob.run (node:internal/modules/esm/module_job:343:25)
```

**Root cause**: npm silently skipped the darwin-x64 optional dependency. This happens when:
- `--no-optional` was used (common on macOS to "speed up" install)
- npm cache corruption from prior failed installs
- Registry flakiness during install

## Dist-tag Architecture

`@openai/codex-darwin-x64` is NOT a separate npm package. It's an alias:

```
"optionalDependencies": {
  "@openai/codex-darwin-x64": "npm:@openai/codex@0.132.0-darwin-x64",
  "@openai/codex-linux-x64":  "npm:@openai/codex@0.132.0-linux-x64",
  "@openai/codex-darwin-arm64": "npm:@openai/codex@0.132.0-darwin-arm64",
  ...
}
```

The `npm:` prefix means "install package `@openai/codex` at version tag `0.132.0-darwin-x64`".

**Verification:**
```bash
npm view @openai/codex optionalDependencies --json
```

## Symlink Anatomy

After a successful install, the global symlink looks like:
```
$(npm config get prefix)/bin/codex
  → $(npm root -g)/@openai/codex/node_modules/@openai/codex-darwin-x64/vendor/x86_64-apple-darwin/codex/codex
```

If any component of this chain is missing (empty `@openai/codex-darwin-x64` dir, missing `vendor/`), the symlink is broken and `which codex` succeeds but running it fails with "No such file or directory".

## Diagnostic Commands

```bash
# Check if optional deps were installed
npm view @openai/codex optionalDependencies --json

# Verify the actual darwin package location
ls -la "$(npm root -g)/@openai/codex/node_modules/@openai/codex-darwin-x64/"

# Check symlink health
file "$(npm config get prefix)/bin/codex"
ls -la "$(npm config get prefix)/bin/codex"

# Check npm config
npm config get prefix
npm config get include   # should be empty (default = install optional deps)
npm config get omit      # should be empty
```

## Fix Workflow

1. Clean stale state:
   ```bash
   mv "$(npm root -g)/@openai" "$(npm root -g)/@openai_stale"
   rm -rf ~/.npm/_npx
   npm cache clean --force
   ```

2. Install darwin binary directly (bypasses optional dep resolution):
   ```bash
   npm install -g @openai/codex@0.132.0-darwin-x64
   ```

3. Or force inclusion of optional deps:
   ```bash
   npm install -g --include=optional @openai/codex@latest
   ```

4. Verify:
   ```bash
   codex --version
   ```

## npmjs.org Bandwidth from China

The npm registry (registry.npmjs.org) can be extremely slow from China —
as low as 16KB/s for large packages. The `@openai/codex` darwin tarball is
~130MB compressed (~211MB uncompressed), so at 16KB/s the download takes
over 2 hours and the connection often drops before completion.

**Solution**: Use the Chinese npm mirror (npmmirror / Alibaba CDN):

```bash
# For global install
npm install -g --registry=https://registry.npmmirror.com @openai/codex@latest

# For local install
npm install --registry=https://registry.npmmirror.com @openai/codex@latest
```

This typically resolves download speed issues entirely. It also works for
`npm view` queries and individual dist-tag installs.

**Also works for direct curl fallback**:
```bash
# npmmirror CDN URL (302 redirect to cdn.npmmirror.com)
TGZ_URL="https://registry.npmmirror.com/@openai/codex/-/codex-0.132.0-darwin-x64.tgz"
curl -L -o /tmp/codex.tgz "$TGZ_URL"
```

## Clean-Directory Install (Avoids Global Node Modules Lockup)

When the global `node_modules/@openai` directory is corrupted from prior
failed installs, any operation on it — `rm -rf`, `mv`, `npm uninstall` —
can time out (>30s) on macOS due to the massive file count. This is
especially common after multiple failed Codex install attempts.

**The clean-directory approach** bypasses global node_modules entirely:

```bash
# 1. Create a fresh workspace
mkdir -p /tmp/codex-install && cd /tmp/codex-install
npm init -y

# 2. Install to this fresh directory (no conflicts, no stale dirs)
npm install --registry=https://registry.npmmirror.com @openai/codex@latest

# 3. Locate the binary (it's in the darwin-x64 package, not the main one)
BINARY=$(find node_modules -name codex -type f -perm +111 | grep darwin | grep -v path)
# Typically: node_modules/@openai/codex-darwin-x64/vendor/x86_64-apple-darwin/codex/codex

# 4. Verify binary size (should be >200MB)
ls -lh "$BINARY"

# 5. Link to global bin
ln -sf "$PWD/$BINARY" "$(npm config get prefix)/bin/codex"

# 6. Verify
codex --version  # should print "codex-cli 0.132.0"
```

**Why this works when global install doesn't**:
- No stale `@openai` directory to conflict with (ENOTEMPTY avoided)
- No npm cache poisoning from prior partial downloads
- npm treats it as a fresh project, resolving deps from scratch
- Combined with npmmirror, completes in <30 seconds

After verifying, you can clean up `/tmp/codex-install` — only the symlink in
the global bin directory is needed at runtime.

## Why `rm -rf` Hangs

macOS with large node_modules trees: `rm -rf` on `$(npm root -g)/@openai` can
hang with thousands of files. Use `mv` to a `_stale` directory instead —
it's atomic and instant. Clean up `_stale` later manually or with a background
`rm -rf`. If even `mv` times out (rare but possible with very corrupted
filesystems), use the clean-directory approach above.

## Truncated Binary from Corrupt npm Cache

**Symptom**: `codex --version` exits with `Killed: 9` (SIGKILL, exit code 137).
`codesign --force --sign -` fails with "main executable failed strict validation".

**Diagnostic**:
```bash
# Check the binary's Mach-O structure
otool -l "$(npm root -g)/@openai/codex/vendor/x86_64-apple-darwin/codex/codex" | head -30
```

**Corrupt output** (look for "past end of file"):
```
segname __TEXT
   vmaddr 0x0000000100000000
   vmsize 0x000000000c988000
  fileoff 0
 filesize 211320832 (past end of file)    ← BINARY IS TRUNCATED
```

The Mach-O header declares a `filesize` of ~211 MB but the actual file on disk is
only 12–15 MB. npm cached a partially-downloaded tarball and reused it on every
subsequent install.

**Root cause**: The `@openai/codex` darwin tarball is large (~211 MB uncompressed).
If a download is interrupted (network flakiness, npm timeout), npm saves the
partial tarball in its content-addressable cache (`~/.npm/_cacache/`). Subsequent
`npm install` commands find the cache entry, verify its integrity hash (which
matches because the tarball itself was complete but the extraction was partial),
and reuse the corrupt entry.

**Fix — bypass npm cache entirely**:
```bash
# 1. Get the direct download URL
TGZ_URL=$(npm view @openai/codex@0.132.0-darwin-x64 dist.tarball)

# 2. Download fresh tarball (bypasses npm cache)
curl -L -o /tmp/codex-darwin.tgz "$TGZ_URL"

# 3. Extract
mkdir -p /tmp/codex-pkg
tar -xzf /tmp/codex-darwin.tgz -C /tmp/codex-pkg

# 4. Copy binary to npm prefix
cp /tmp/codex-pkg/package/vendor/x86_64-apple-darwin/codex/codex \
   "$(npm config get prefix)/bin/codex"
chmod +x "$(npm config get prefix)/bin/codex"

# 5. Verify
"$(npm config get prefix)/bin/codex" --version
```

**Alternatively, if npm cache is also too large to clean**, surgically remove
only the codex cache entries by content hash. Find the hash:
```bash
npm cache ls 2>/dev/null | grep codex   # may not work on npm 10+
```
If that fails, identify the integrity hash from the package metadata and delete
the corresponding `_cacache/content-v2/sha512/<hash>` entry.

**Prevention**: After a successful install, verify the binary size is reasonable:
```bash
SIZE=$(stat -f%z "$(npm root -g)/@openai/codex/vendor/x86_64-apple-darwin/codex/codex")
# Should be >200 MB. If <50 MB, the binary is truncated.
if [ "$SIZE" -lt 50000000 ]; then
  echo "WARNING: Binary appears truncated ($SIZE bytes)"
fi
```
