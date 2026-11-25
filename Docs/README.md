# Ship It by Noon: The one-hour Database App

You will build a small, real web app from your own idea, starting from an empty folder, by directing an AI coding assistant. Nothing in this repository is an app: it holds only **places for things** and **the rules your AI follows**, plus the location of the class database. The idea is yours, the code comes from you directing the AI, and you run it, check it, and fix it.

```
web/index.html  -->  server/server.js  -->  SQL Server (class server, your <NetID>_myapp database)
the page you see     the middle tier:        the data
                     runs SQL, returns JSON
```

The page never talks to the database. It asks your server (`/api/...`), the server runs SQL with the user's input as a **parameter**, and sends the rows back as JSON.

## Use Copilot Free (no student verification needed)

Student verification can be slow or fail with an unhelpful error. You don't need it today: **Copilot Free** works right away.

1. In VS Code, hover over the **Copilot icon in the Status Bar** (bottom of the window) and click **Use AI Features**. (Or open the Accounts menu, bottom left, and sign in with GitHub.)
2. Sign in with your GitHub account and follow the prompts. If your account has no Copilot plan, signing in **enrolls you in Copilot Free** automatically.
3. Open the Chat panel and choose **Agent** mode.

If VS Code still won't start Copilot: go to <https://github.com/settings/copilot>, click **Start using Copilot Free**, then sign in again in VS Code. Copilot Free has a monthly allowance; the Copilot icon in the Status Bar shows how much you've used.

Sources: [Set up Copilot in VS Code](https://code.visualstudio.com/docs/setup/copilot), [Get started with a Copilot plan](https://docs.github.com/en/copilot/how-tos/manage-your-account/get-started-with-a-copilot-plan).

**Backup if Copilot won't work at all: Google Antigravity.** A free (for individuals) editor built on VS Code with an AI agent, for Mac, Windows, and Linux, signed in with a Google account. Download at <https://antigravity.google/download>, open your cloned folder in it, and use its agent with the same prompts. ([Google's announcement](https://developers.googleblog.com/build-with-google-antigravity-our-new-agentic-development-platform/))

## Steps

1. **Set up VS Code (10 min).** [prompts/1_setup_vscode.md](prompts/1_setup_vscode.md)
2. **Choose an app domain (5 min).** [prompts/2_domain.md](prompts/2_domain.md)
3. **Set up your laptop environment (15 min).** [prompts/3_environment.md](prompts/3_environment.md). Turn in a screenshot.
4. **Build your app from a user story (45 min).** [prompts/4_build.md](prompts/4_build.md). Turn in a screenshot and your repository link.

**Extra:** [host your app permanently on UW's servers](prompts/extra_host_on_vergil.md).

The prompts are starting points: change them to fit your idea. When the AI gets something wrong, tell it exactly what you saw.

## What is in this repository

| Location | What goes there | Who writes it |
| --- | --- | --- |
| `IDEA.md` | Your domain and user story | You |
| `PROMPTS.md` | A short log of what you asked the AI and what you fixed | You |
| `web/`, `server/`, `db/` | The page, the middle tier, the SQL | The AI, checked by you |
| `prompts/` | The prompt for each step | Given |
| `AGENTS.md` | Rules the AI reads automatically: the architecture, parameters only, no passwords in code. Copies in `.github/copilot-instructions.md` (Copilot) and `CLAUDE.md` (Claude Code) | Given |
| `DATASETS.md` | Real public data you could use instead of made-up rows | Given |
| `scripts/` | `npm run create-db` (creates your database) and `npm run check` (tests the connection) | Given |
| `.env.example` | Where the class database is. Copy it to `.env` with the password | Given |

## Copilot or Claude Code?

| | GitHub Copilot (what we use in class) | Claude Code (what the instructor uses) |
| --- | --- | --- |
| Where it runs | Chat panel inside VS Code; Agent mode edits files and runs commands | Terminal, or the Claude Code extension in VS Code |
| Models | Several providers; the free Student plan picks the model for you (Auto) | Anthropic's Claude models only, which you choose |
| Price | Free for verified students (Copilot Student); Copilot Free for everyone else | Needs a paid Claude plan: Pro is about $20/month; Max costs more |
| Links | <https://github.com/features/copilot>, <https://education.github.com/pack> | <https://claude.com/product/claude-code>, <https://claude.com/pricing> |

Both read a project rules file, and both make mistakes: checking the result is your job.

## Troubleshooting

- **"getaddrinfo ENOTFOUND" or a timeout**: you are not on the UW network. Connect to Husky OnNet.
- **"Login failed for user" right after setup**: your database may not exist yet. Run `npm run create-db`.
- **"Login failed for user" otherwise**: the password in `.env` is wrong or has extra spaces.
- **Everyone shares one database login today**, so other students could see your database. Don't put anything private in it.
- **`EADDRINUSE` when starting**: a server is already running in another terminal. Stop it with Ctrl+C, or set `PORT=3001` in `.env`.
- **The page did not change after an edit**: restart the server (Ctrl+C, then `npm start`) and reload the page.
