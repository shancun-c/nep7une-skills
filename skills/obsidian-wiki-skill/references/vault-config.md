# Vault Configuration

> Machine-specific paths and settings for this user's Obsidian vault.  
> Updated: 2026-05-28

## Vault Path

```
/Users/nep7une/Library/CloudStorage/GoogleDrive-wenweikun@gmail.com/其他计算机/我的计算机/the_ai_obsidian
```

## Git Remote

```
git@github.com:shancun-c/the_ai_obsidian.git
```

## Safe Push Workflow

**Never run git commands directly in the vault directory.** The vault has no `.git` directory by design.

Instead, use the clone+rsync pattern from the independent git working copy:

```bash
# Sync vault into git clone, commit, and push
cd ~/code/the_ai_obsidian
rsync -a --exclude='.git' --exclude='.obsidian' --exclude='.DS_Store' \
  ~/Library/CloudStorage/GoogleDrive-*/其他计算机/我的计算机/the_ai_obsidian/ ./
git add -A
git commit -m "..."
git push origin main
```

## Pitfalls

1. **Never `git reset --hard` on vault files.** The local vault is the source of truth; the remote is often stale. `reset --hard` replaces local files with outdated remote versions.
2. **SSH clone may time out on large repos.** Use `git -c http.postBuffer=524288000` for large repos with many binary files.
3. **Google Drive users**: if an accidental `reset --hard` occurs, use Finder → Revert To to restore individual files from version history.
