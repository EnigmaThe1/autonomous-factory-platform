"""Platform settings endpoints — provider config, API keys, connectors."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from af_core.config import settings as runtime_settings
from af_core.database import get_db
from af_core.models.settings import PlatformSetting

# Maps DB setting keys to runtime Settings attributes
_RUNTIME_BINDINGS: dict[str, str] = {
    "execution.workspace_root": "workspace_root",
    "execution.default_timeout_seconds": "timeout_seconds",
}

router = APIRouter(prefix="/api/settings", tags=["settings"])

# Default settings seeded on first access
_DEFAULTS: list[dict] = [
    # --- Provider routing ---
    {
        "category": "providers",
        "key": "providers.default_provider",
        "value": "openai",
        "description": "Default LLM provider (openai, anthropic, local)",
        "is_secret": False,
    },
    {
        "category": "providers",
        "key": "providers.planner_model",
        "value": "gpt-4o",
        "description": "Model for Planner agent — high reasoning quality",
        "is_secret": False,
    },
    {
        "category": "providers",
        "key": "providers.researcher_model",
        "value": "gpt-4o",
        "description": "Model for Researcher agent — strong retrieval",
        "is_secret": False,
    },
    {
        "category": "providers",
        "key": "providers.implementer_model",
        "value": "gpt-4o",
        "description": "Model for Implementer agent — balanced coding",
        "is_secret": False,
    },
    {
        "category": "providers",
        "key": "providers.reviewer_model",
        "value": "gpt-4o",
        "description": "Model for Reviewer agent — high judgment",
        "is_secret": False,
    },
    {
        "category": "providers",
        "key": "providers.validator_model",
        "value": "gpt-4o",
        "description": "Model for Validator agent — structured output",
        "is_secret": False,
    },
    {
        "category": "providers",
        "key": "providers.compiler_model",
        "value": "gpt-4o",
        "description": "Model for Mission Compiler — ambiguity handling",
        "is_secret": False,
    },
    {
        "category": "providers",
        "key": "providers.fallback_provider",
        "value": "",
        "description": "Fallback provider when primary fails",
        "is_secret": False,
    },
    # --- API keys ---
    {
        "category": "api_keys",
        "key": "api_keys.openai_api_key",
        "value": "",
        "description": "OpenAI API key",
        "is_secret": True,
    },
    {
        "category": "api_keys",
        "key": "api_keys.anthropic_api_key",
        "value": "",
        "description": "Anthropic API key",
        "is_secret": True,
    },
    {
        "category": "api_keys",
        "key": "api_keys.google_api_key",
        "value": "",
        "description": "Google AI API key",
        "is_secret": True,
    },
    {
        "category": "api_keys",
        "key": "api_keys.local_endpoint",
        "value": "http://localhost:11434",
        "description": "Local model endpoint (Ollama, vLLM, etc.)",
        "is_secret": False,
    },
    # --- Execution ---
    {
        "category": "execution",
        "key": "execution.default_step_budget",
        "value": "50",
        "description": "Default max steps per mission",
        "is_secret": False,
    },
    {
        "category": "execution",
        "key": "execution.default_timeout_seconds",
        "value": "3600",
        "description": "Default mission timeout in seconds",
        "is_secret": False,
    },
    {
        "category": "execution",
        "key": "execution.max_retries",
        "value": "3",
        "description": "Max retries for transient failures",
        "is_secret": False,
    },
    {
        "category": "execution",
        "key": "execution.workspace_root",
        "value": ".",
        "description": "Root workspace directory",
        "is_secret": False,
    },
    {
        "category": "execution",
        "key": "execution.isolation_mode",
        "value": "workspace",
        "description": "Execution isolation (workspace, container, none)",
        "is_secret": False,
    },
    # --- Connectors ---
    {
        "category": "connectors",
        "key": "connectors.github_token",
        "value": "",
        "description": "GitHub personal access token",
        "is_secret": True,
    },
    {
        "category": "connectors",
        "key": "connectors.github_org",
        "value": "",
        "description": "Default GitHub organization",
        "is_secret": False,
    },
    {
        "category": "connectors",
        "key": "connectors.jira_url",
        "value": "",
        "description": "Jira instance URL",
        "is_secret": False,
    },
    {
        "category": "connectors",
        "key": "connectors.jira_token",
        "value": "",
        "description": "Jira API token",
        "is_secret": True,
    },
    {
        "category": "connectors",
        "key": "connectors.slack_webhook",
        "value": "",
        "description": "Slack notification webhook URL",
        "is_secret": True,
    },
    # --- Safety ---
    {
        "category": "safety",
        "key": "safety.require_approval_for_deploy",
        "value": "true",
        "description": "Require human approval before deployment actions",
        "is_secret": False,
    },
    {
        "category": "safety",
        "key": "safety.require_approval_for_mutations",
        "value": "false",
        "description": "Require approval for file mutations",
        "is_secret": False,
    },
    {
        "category": "safety",
        "key": "safety.protected_paths",
        "value": ".env,.git/config,credentials",
        "description": "Comma-separated protected file patterns",
        "is_secret": False,
    },
    {
        "category": "safety",
        "key": "safety.max_file_size_mb",
        "value": "100",
        "description": "Max upload file size in MB",
        "is_secret": False,
    },
]


class SettingUpdate(BaseModel):
    value: str


class SettingResponse(BaseModel):
    id: str
    category: str
    key: str
    value: str
    is_secret: bool
    description: str

    model_config = {"from_attributes": True}


class SettingsByCategoryResponse(BaseModel):
    categories: dict[str, list[SettingResponse]]


async def _ensure_defaults(db: AsyncSession) -> None:
    """Seed default settings if table is empty."""
    result = await db.execute(select(PlatformSetting).limit(1))
    if result.scalar_one_or_none() is not None:
        return
    for d in _DEFAULTS:
        db.add(PlatformSetting(**d))
    await db.commit()


def _mask(setting: PlatformSetting) -> SettingResponse:
    """Return response with secret values masked."""
    val = setting.value
    if setting.is_secret and val:
        val = val[:4] + "****" + val[-4:] if len(val) > 8 else "****"
    return SettingResponse(
        id=setting.id,
        category=setting.category,
        key=setting.key,
        value=val,
        is_secret=setting.is_secret,
        description=setting.description,
    )


@router.get("", response_model=SettingsByCategoryResponse)
async def list_settings(db: AsyncSession = Depends(get_db)):
    await _ensure_defaults(db)
    result = await db.execute(
        select(PlatformSetting).order_by(PlatformSetting.category, PlatformSetting.key)
    )
    settings = result.scalars().all()
    categories: dict[str, list[SettingResponse]] = {}
    for s in settings:
        categories.setdefault(s.category, []).append(_mask(s))
    return SettingsByCategoryResponse(categories=categories)


@router.get("/{category}", response_model=list[SettingResponse])
async def list_category(category: str, db: AsyncSession = Depends(get_db)):
    await _ensure_defaults(db)
    result = await db.execute(
        select(PlatformSetting)
        .where(PlatformSetting.category == category)
        .order_by(PlatformSetting.key)
    )
    return [_mask(s) for s in result.scalars().all()]


@router.put("/{setting_id}", response_model=SettingResponse)
async def update_setting(setting_id: str, body: SettingUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PlatformSetting).where(PlatformSetting.id == setting_id))
    setting = result.scalar_one_or_none()
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    setting.value = body.value
    await db.commit()
    await db.refresh(setting)

    # Propagate to runtime if this key has a binding
    if setting.key in _RUNTIME_BINDINGS:
        attr = _RUNTIME_BINDINGS[setting.key]
        setattr(runtime_settings, attr, body.value)

    return _mask(setting)


@router.post("", response_model=SettingResponse)
async def create_setting(
    category: str,
    key: str,
    value: str = "",
    description: str = "",
    is_secret: bool = False,
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(PlatformSetting).where(PlatformSetting.key == key))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Setting key already exists")
    setting = PlatformSetting(
        category=category, key=key, value=value, description=description, is_secret=is_secret
    )
    db.add(setting)
    await db.commit()
    await db.refresh(setting)
    return _mask(setting)


@router.delete("/{setting_id}")
async def delete_setting(setting_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PlatformSetting).where(PlatformSetting.id == setting_id))
    setting = result.scalar_one_or_none()
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    await db.delete(setting)
    await db.commit()
    return {"deleted": True}
