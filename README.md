# Sora Storyboard Workflow Generator

A reusable workflow that transforms marketing briefs into fully-formatted Sora 2 storyboard prompts for Kie.ai.

## Features

- **Smart Clarification**: Automatically identifies gaps in your brief and asks clarifying questions
- **Style-Aware**: Supports multiple vibes (Wolf of Wall Street, TikTok UGC, Wes Anderson, Documentary, etc.)
- **Structured Output**: Generates prompts with all required sections (SHOT, SUBJECT, SCENE, VISUAL DETAILS, ACTION & CAMERA, CINEMATOGRAPHY, AUDIO, STYLE)
- **Platform Optimization**: Tailors content for different platforms (TikTok, Instagram, YouTube, etc.)

## Quick Start

```bash
python sora_workflow.py
```

Then follow the interactive prompts, or provide a brief directly:

```bash
python sora_workflow.py --brief "30-second ad, sarcastic, CPC went up again, target: media buyers, platform: TikTok, style: Wolf of Wall Street"
```

## Brief Format

Your brief can include:
- **Duration**: e.g., "30-second", "60s", "15 seconds"
- **Tone**: e.g., "sarcastic", "serious", "playful", "dramatic"
- **Message**: The core idea or pain point
- **Target Audience**: Who you're speaking to
- **Platform**: TikTok, Instagram, YouTube, etc.
- **Style/Vibe**: Reference films, directors, or content styles

## Output Format

The workflow generates a complete Sora storyboard with:
- SHOT (number and scene designation)
- SUBJECT (who/what is in frame)
- SCENE (location and setting)
- VISUAL DETAILS (specific visual elements)
- ACTION & CAMERA (movement and camera work)
- CINEMATOGRAPHY (lighting, framing, technical specs)
- AUDIO (dialogue, music, sound design)
- STYLE (overall aesthetic and references)

## Examples

See `examples/` directory for sample briefs and their generated storyboards.
