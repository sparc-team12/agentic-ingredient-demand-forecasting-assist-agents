"""Run-profile definitions for the agent runner.

Each profile is an explicit tool allowlist passed to `claude -p ... --allowedTools`.
Nothing here ever uses --dangerously-skip-permissions / bypassPermissions -- any
tool call not named in `allowed_tools` is auto-denied (via --permission-prompts none),
not silently allowed and not left hanging on an unanswerable prompt.
"""

from dataclasses import dataclass, field


READ_ONLY_CONFLUENCE_TOOLS = [
    "mcp__claude_ai_Atlassian_Rovo__getConfluencePage",
    "mcp__claude_ai_Atlassian_Rovo__searchConfluenceUsingCql",
    "mcp__claude_ai_Atlassian_Rovo__getAccessibleAtlassianResources",
    "mcp__claude_ai_Atlassian_Rovo__getConfluenceSpaces",
    "mcp__claude_ai_Atlassian_Rovo__getConfluencePageFooterComments",
    "mcp__claude_ai_Atlassian_Rovo__getContentFormatGuide",
]

CONFLUENCE_WRITE_TOOLS = [
    "mcp__claude_ai_Atlassian_Rovo__createConfluencePage",
    "mcp__claude_ai_Atlassian_Rovo__updateConfluencePage",
    "mcp__claude_ai_Atlassian_Rovo__getPagesInConfluenceSpace",
    "mcp__claude_ai_Atlassian_Rovo__getConfluencePageDescendants",
]

LOCAL_FILE_TOOLS = ["Read", "Write", "Edit", "Glob", "Grep"]


@dataclass(frozen=True)
class Profile:
    key: str
    label: str
    description: str
    prompt: str
    allowed_tools: list[str]
    permission_mode: str = "acceptEdits"
    requires_confirmation: bool = False
    confirmation_text: str = ""


PROFILES: dict[str, Profile] = {
    "generate": Profile(
        key="generate",
        label="Generate Architecture (local only)",
        description=(
            "Resolves the PRD (local file, or read-only fetch from Confluence if missing), "
            "generates ARCH-XXX, generates the Solution Architecture / Security Architecture / "
            "Technology Stack drafts, and runs validation-review. Cannot publish -- Confluence "
            "write tools are not in this profile's allowlist, so the publish step is cleanly "
            "denied rather than silently skipped or hung."
        ),
        prompt="/generate-architecture",
        allowed_tools=LOCAL_FILE_TOOLS + READ_ONLY_CONFLUENCE_TOOLS,
        permission_mode="acceptEdits",
        requires_confirmation=False,
    ),
    "publish": Profile(
        key="publish",
        label="Publish Architecture Suite to Confluence",
        description=(
            "Re-runs /generate-architecture with Confluence write access enabled, so the "
            "already-drafted and validated documents can actually be published once you've "
            "reviewed them. Only run this after reviewing the drafts produced by the "
            "'Generate' profile and the validation-review findings."
        ),
        prompt="/generate-architecture",
        allowed_tools=LOCAL_FILE_TOOLS + READ_ONLY_CONFLUENCE_TOOLS + CONFLUENCE_WRITE_TOOLS,
        permission_mode="acceptEdits",
        requires_confirmation=True,
        confirmation_text=(
            "I have reviewed the generated Solution Architecture / Security Architecture / "
            "Technology Stack drafts and the validation-review findings (including every "
            "[SECURITY REVIEW REQUIRED] marker), and I approve publishing them to Confluence."
        ),
    ),
    "custom": Profile(
        key="custom",
        label="Custom prompt (advanced)",
        description=(
            "Runs an arbitrary prompt/command (e.g. a single agent by name, or a different "
            "slash command) with the local-file-only allowlist. Confluence writes and Bash "
            "are not included -- add them explicitly below if a specific run genuinely needs them."
        ),
        prompt="",
        allowed_tools=LOCAL_FILE_TOOLS + READ_ONLY_CONFLUENCE_TOOLS,
        permission_mode="acceptEdits",
        requires_confirmation=False,
    ),
}
