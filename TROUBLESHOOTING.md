# Claude Code Web - Quick Troubleshooting Reference

**Quick Links:**
- [Common Errors](#common-errors)
- [Verification Checklist](#verification-checklist)
- [Success Indicators](#success-indicators)
- [Full Guide](SETUP.md)

---

## Common Errors

### ❌ "Clojure not found"

**Fix:**
```bash
make claude-code-web-setup
```

Or manually:
```bash
mkdir -p ~/.local && curl -L -O https://github.com/clojure/brew-install/releases/latest/download/linux-install.sh && chmod +x linux-install.sh && ./linux-install.sh --prefix ~/.local && rm linux-install.sh && mkdir -p ~/bin && ln -sf ~/.local/bin/clojure ~/bin/clojure && ln -sf ~/.local/bin/clj ~/bin/clj
```

---

### ❌ ".proxy-java-shim.env not found"

**Fix:**
```bash
cp .proxy-java-shim.env.template .proxy-java-shim.env
```

Or from this repo:
```bash
cp docs/claude-code-web-repo/.proxy-java-shim.env .
```

---

### ❌ "UnknownHostException: repo1.maven.org"

**Cause:** Wrong proxy configuration or proxy shim not running

**Check which proxy is being used:**
```bash
# Look for this in output:
Picked up JAVA_TOOL_OPTIONS: -Dhttp.proxyHost=127.0.0.1 -Dhttp.proxyPort=15080
# ✅ Good - using local proxy shim

# OR
Picked up JAVA_TOOL_OPTIONS: -Dhttp.proxyHost=21.0.0.169 ...
# ❌ Bad - using direct Claude proxy (will fail)
```

**Fix:**
```bash
# Ensure you're using the shim:
make claude-sandbox-tests  # This auto-starts the shim

# Or manually:
make proxy-shim-start
. ./.proxy-java-shim.env
# ... run your build ...
make proxy-shim-stop
```

---

### ❌ "Failed to read artifact descriptor"

**Cause:** Corrupt Maven cache (empty directories from failed downloads)

**Fix:**
```bash
rm -rf ~/.m2/repository .cpcache
make claude-sandbox
```

---

### ❌ "503 Service Unavailable"

**Cause:** Maven Central temporarily rate-limiting (NOT a config issue)

**Verify proxy is working:**
Look for successful downloads before the 503:
```
Downloading: org/clojure/data.json/2.5.0/data.json-2.5.0.pom from central ✅
Downloading: lambdaisland/kaocha/1.91.1392/kaocha-1.91.1392.pom from clojars ✅
```

If you see these, setup is correct! Just retry:
```bash
make claude-sandbox
```

---

### ❌ "Proxy shim already running"

**Fix:**
```bash
make proxy-shim-stop
make claude-sandbox
```

---

### ❌ "401 Unauthorized"

**Cause:** Proxy shim not running or Java not configured to use it

**Fix:**
```bash
make proxy-shim-stop
make claude-sandbox-tests  # Auto-starts shim
```

---

## Verification Checklist

Run through these in order:

```bash
# 1. Clojure installed?
clojure --version
# Should show: Clojure CLI version 1.12.3.1577
# If not: make claude-code-web-setup

# 2. Proxy config exists?
ls -la .proxy-java-shim.env
# If not: cp docs/claude-code-web-repo/.proxy-java-shim.env .

# 3. Maven settings exist?
ls -la ~/.m2/settings.xml
# If not: cp docs/claude-code-web-repo/settings.xml ~/.m2/

# 4. Proxy shim script exists?
ls -la script/proxy_shim.py
# If not: cp docs/claude-code-web-repo/proxy_shim.py script/

# 5. Clear corrupt cache?
rm -rf ~/.m2/repository .cpcache

# 6. Run complete verification
make claude-sandbox-verify

# 7. Run tests
make claude-sandbox
```

---

## Success Indicators

✅ **Setup is working when you see:**

```
1. Proxy shim starts:
   ✓ Proxy shim started on 127.0.0.1:15080 (pid 12345)

2. Java uses correct proxy:
   Picked up JAVA_TOOL_OPTIONS: -Dhttp.proxyHost=127.0.0.1 -Dhttp.proxyPort=15080

3. Downloads succeed:
   Downloading: org/clojure/clojure/1.12.0/clojure-1.12.0.pom from central
   Downloading: lambdaisland/kaocha/1.91.1392/kaocha-1.91.1392.pom from clojars

4. Tests pass:
   246 tests, 3759 assertions, 0 failures.

5. Final success:
   🎉 All Claude Code sandbox checks passed!
```

---

## Error Pattern Quick Reference

| Error | Likely Cause | Quick Fix |
|-------|-------------|-----------|
| `Clojure not found` | Not installed | `make claude-code-web-setup` |
| `.proxy-java-shim.env not found` | File missing | `cp docs/claude-code-web-repo/.proxy-java-shim.env .` |
| `UnknownHostException` | Wrong proxy | Check JAVA_TOOL_OPTIONS shows 127.0.0.1:15080 |
| `Failed to read artifact` | Corrupt cache | `rm -rf ~/.m2/repository .cpcache` |
| `503 Service Unavailable` | Maven Central rate limit | Just retry |
| `Proxy shim already running` | Leftover process | `make proxy-shim-stop` |
| `401 Unauthorized` | Shim not running | `make claude-sandbox-tests` |

---

## Emergency Reset

If nothing works, start fresh:

```bash
# 1. Stop everything
make proxy-shim-stop

# 2. Clean all caches
rm -rf ~/.m2/repository .cpcache

# 3. Remove config files
rm -f .proxy-java-shim.env .proxy-shim.pid

# 4. Reinstall from scratch
make claude-code-web-setup
cp docs/claude-code-web-repo/.proxy-java-shim.env .
cp docs/claude-code-web-repo/settings.xml ~/.m2/

# 5. Run complete workflow
make claude-sandbox
```

---

## Still Not Working?

1. **Check proxy shim logs:**
   ```bash
   cat /tmp/proxy-shim.log
   ```

2. **Verify HTTP_PROXY is set:**
   ```bash
   echo $HTTP_PROXY
   # Should show: http://container_...@21.0.0.169:15004
   ```

3. **Test proxy shim manually:**
   ```bash
   make proxy-shim-start
   curl -x http://127.0.0.1:15080 https://repo1.maven.org/maven2/
   make proxy-shim-stop
   # Should return HTML (not an error)
   ```

4. **Read the full guide:**
   [SETUP.md](SETUP.md) has detailed explanations for every issue

---

## Quick Command Reference

```bash
# Verification
make claude-sandbox-verify    # Check setup
make claude-sandbox           # Complete workflow

# Testing
make claude-sandbox-tests     # Run tests (auto proxy)
make runtests-shim           # Run tests (manual proxy)

# Proxy Control
make proxy-shim-start        # Start proxy shim
make proxy-shim-stop         # Stop proxy shim

# Setup
make claude-code-web-setup   # Install Clojure

# Cleanup
make proxy-shim-stop         # Stop proxy
rm -rf ~/.m2/repository      # Clear Maven cache
rm -rf .cpcache              # Clear Clojure cache
```

---

## Time to Success

- **First time (clean install):** 3-5 minutes
- **With cached dependencies:** <10 seconds
- **After troubleshooting:** Usually <1 minute

---

**Remember:** Like the movie Memento, start from the beginning if you're lost. Run `make claude-sandbox` and it handles everything! 🎬
