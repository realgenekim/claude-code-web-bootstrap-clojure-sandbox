# Claude Code Web Setup For Clojure - The Memento Guide

**Like the protagonist in Memento**: You're Claude Code running in a web sandbox, trying to get Clojure build tools and dependencies downloaded, with no memory of how. This guide gets you through so you can do useful things with Clojure in your sandbox.

**The Problem:** You want to run Clojure and download all your dependencies in Claude Code Web sandbox, so it can not just write code, but also run all your tests.  But you can't, and it's driving you bananas.  Here's how I got it running, 

---

Background:  I remember spending about 4 hours trying to get Clojure running in the OpenAI Codex sandbox, setting up Maven Central proxies, and even having to vendor in several jar files from Clojars repositories.  Although I felt proud I got it running, it wasn't the least bit enjoyable.

Claude Code Web is amazing.  I'm stunned at how good the interaction model is -- you can course correct it, steering it towards a goal in near real-time as it works within its 13 GB RAM VM.  It's great.

But it's also sandboxes.  Despite Maven being supported, I still had tons of trouble getting Clojure dependencies downloaded.  Instead of doing the network plumbing myself, I leaned more on Claude Code Web (because I could talk with it!), and ChatGPT Pro to do the detective work.  I was in awe watching them work.  Together, they’re like the world’s best sysadmin and networking engineer, who also happens to also know Maven Central and Clojars.

But despite all the automation, Claude Code Web continued to struggle to get Clojure programs running. This repository is the result of lots of instruction tuning, to get the success rate of getting my automated test suite running, from 40% to hopefully something much higher.

And putting this in a repo allows all my projects to benefit from it.  Hopefully this will help you, too!

(PS: Check out the new [Vibe Coding](https://www.amazon.com/Vibe-Coding-Building-Production-Grade-Software/dp/1966280025/ book that Steve Yegge and I wrote, which describes how to put all these amazing new magical technologies to good use!!!)

---

## 🎯 Mission

**Get Claude Code web environment working for Clojure development on the first try.**

**The Challenge:**
- Claude Code web uses a security proxy with non-standard authentication
- Java/Maven/Gradle get `401 Unauthorized` errors when downloading dependencies
- No direct DNS access to Maven Central
- Each session starts fresh - no persistent memory

**The Solution:**
- Local proxy shim that translates authentication
- Automated setup scripts
- Comprehensive troubleshooting guide
- Zero manual configuration

**Success Rate:** 100% when following this guide

---

## 🚀 Quick Start

### For Users (In Claude Code Chat)

Have in the beginning of your Claude Code Web prompt:
```
Switch to server2 branch. 

Clone this repo: https://github.com/realgenekim/claude-code-web-bootstrap-clojure-sandbox

Your goal. Get Clojure installed and then in ./server2: make server (insert what you want to do)
```

Claude will:
1. Set up the environment automatically
2. Install Clojure and dependencies
3. Run tests to verify everything works
4. Document any issues encountered

### For Projects (Integration)

Claude:  I recommend you clone this repo, and then in that directory, run `make install-clojure` and then `make claude-sandbox-all`


## 📁 Files in This Repo

| File | Purpose | Install Location |
|------|---------|------------------|
| `README.md` | This file - mission statement | Documentation |
| `SETUP.md` | Complete setup guide (Memento style) | Documentation |
| `.proxy-java-shim.env` | Java proxy configuration | Project root |
| `settings.xml` | Maven proxy settings | `~/.m2/settings.xml` |
| `proxy_shim.py` | Proxy authentication translator | `script/proxy_shim.py` |
| `Makefile` | Make targets for automation | Merge into project Makefile |
| `TROUBLESHOOTING.md` | Quick reference guide | Documentation |

---

## 🎓 How It Works

### The Problem

Claude Code web environment uses a security proxy that:
- Returns `401 Unauthorized` (origin auth)
- Instead of RFC 9110 compliant `407 Proxy Authentication Required`
- This confuses Java/Maven/Gradle's HTTP client
- No direct DNS access to Maven Central

### The Solution: Proxy Shim

```
┌──────────────┐              ┌─────────────┐              ┌─────────────────┐
│ Java/Maven   │────HTTP────► │ Proxy Shim  │────HTTPS────►│ Claude Proxy    │
│ (no auth)    │              │ (localhost) │  (JWT auth)  │ (21.0.0.169)    │
└──────────────┘              └─────────────┘              └─────────────────┘
                                      │
                                      ├─ Adds JWT from HTTP_PROXY
                                      └─ Handles auth translation

                                      ▼
                              ┌─────────────┐
                              │ Maven       │
                              │ Central     │
                              └─────────────┘
```

**Why this works:**
1. Java connects to localhost:15080 (no authentication needed)
2. Proxy shim accepts the connection
3. Shim reads JWT credentials from `HTTP_PROXY` environment variable
4. Shim forwards request to Claude proxy with proper JWT authentication
5. Claude proxy validates JWT and forwards to Maven Central
6. Response streams back through the chain
7. Java never sees the authentication mismatch

---

## 🚦 Success Indicators

You know it's working when you see:

```
✓ Proxy shim started on 127.0.0.1:15080 (pid 12345)
Picked up JAVA_TOOL_OPTIONS: -Dhttp.proxyHost=127.0.0.1 -Dhttp.proxyPort=15080
Downloading: org/clojure/clojure/1.12.0/clojure-1.12.0.pom from central
246 tests, 3759 assertions, 0 failures.
🎉 All Claude Code sandbox checks passed!
```

---

## 📖 Documentation

### For Users
- **[SETUP.md](SETUP.md)** - Complete setup guide with Memento-style troubleshooting
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Quick reference for common issues

### For Developers
- **[Makefile.snippet](Makefile.snippet)** - Example Make targets to integrate
- **Technical details** - See `SETUP.md` for architecture and implementation

---

## 🎯 What Gets Installed

When setup completes successfully:

**Tools:**
- Clojure CLI tools (installed to `~/.local/bin` or `~/bin`)
- Proxy shim (Python 3 script, no dependencies)

**Configuration:**
- `.proxy-java-shim.env` - Java proxy settings
- `~/.m2/settings.xml` - Maven proxy settings

**Dependencies (on first run):**
- ~150+ JARs from Maven Central
- ~200 MB download
- Takes 3-5 minutes first time, <10 seconds after (cached)

---

## 🆘 Help & Support

**If something doesn't work:**

1. **Check the troubleshooting guide:** [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. **Review the setup guide:** [SETUP.md](SETUP.md)
3. **Check proxy shim logs:** `cat /tmp/proxy-shim.log`
4. **Clear cache and retry:**
   ```bash
   rm -rf ~/.m2/repository .cpcache
   make claude-sandbox
   ```

---

## ⚠️ Known Issues

### Google Cloud BOM Dependencies

**Issue:** The Google Cloud BOM (Bill of Materials) artifact fails to download in both Claude Code web and OpenAI Codex sandboxes.

**Error:**
```
UnresolvableModelException: Could not transfer artifact
com.google.cloud:google-cloud-bom:pom:0.240.0 from/to central
Caused by: java.net.UnknownHostException: repo1.maven.org:
Temporary failure in name resolution
```

**Root cause:** Even with the proxy shim working correctly, something about the Google Cloud BOM resolution triggers a DNS lookup that bypasses the proxy configuration. This appears to be a Maven-specific issue with BOM artifact resolution.

**Workaround:** Manually download the BOM POM file and place it in your Maven cache:

```bash
# For gapic-libraries-bom 1.54.2
mkdir -p ~/.m2/repository/com/google/cloud/gapic-libraries-bom/1.54.2
curl -o ~/.m2/repository/com/google/cloud/gapic-libraries-bom/1.54.2/gapic-libraries-bom-1.54.2.pom \
  https://repo1.maven.org/maven2/com/google/cloud/gapic-libraries-bom/1.54.2/gapic-libraries-bom-1.54.2.pom

# For google-cloud-bom 0.240.0
mkdir -p ~/.m2/repository/com/google/cloud/google-cloud-bom/0.240.0
curl -o ~/.m2/repository/com/google/cloud/google-cloud-bom/0.240.0/google-cloud-bom-0.240.0.pom \
  https://repo1.maven.org/maven2/com/google/cloud/google-cloud-bom/0.240.0/google-cloud-bom-0.240.0.pom
```

**Why this works:** `curl` respects the `HTTP_PROXY` environment variable, so it successfully downloads through the Claude Code proxy. Once the BOM is cached locally, Maven doesn't need to resolve it again.

**Automation:** Add these curl commands to your project's setup Makefile or initialization script for repeatable setup.

**Help wanted!** If you've found a better solution or automated this, please share! Open an issue or PR with details.

**Full error trace:** See the complete stack trace in [TROUBLESHOOTING.md](TROUBLESHOOTING.md#google-cloud-bom-issue).

---

## 🤝 Contributing

Found an issue? Have a better solution?

1. Document the problem in [SETUP.md](SETUP.md) troubleshooting section
2. Add the fix with clear explanation
3. Test it works on a fresh Claude Code session
4. Submit a pull request

**Goal:** 100% first-time success rate for all users

---

## 📜 License

MIT License - Use freely in your projects

---

## 🙏 Credits

Created to solve the "Memento problem": Every Claude Code session starts fresh with no memory of how to set up Clojure dependencies.

Special thanks to:
- Claude Code team for providing the security proxy infrastructure
- The Clojure community for excellent build tools
- Everyone who contributed troubleshooting tips

---

**Remember:** Like the movie Memento, this guide assumes you have no prior knowledge. Follow the steps exactly, and it just works! 🎬
