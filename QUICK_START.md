# Quick Start Guide

## Run the Workflow

```bash
python sora_workflow.py --brief "YOUR BRIEF HERE"
```

## Example Briefs

### 1. Wolf of Wall Street Style (Sarcastic B2B)
```bash
python sora_workflow.py --brief "30-second ad, sarcastic, CPC went up again, target: media buyers, platform: TikTok, style: Wolf of Wall Street"
```

### 2. TikTok UGC Style
```bash
python sora_workflow.py --brief "15-second ad, casual, morning routine hack, target: busy professionals, platform: TikTok, style: TikTok UGC"
```

### 3. Documentary Style
```bash
python sora_workflow.py --brief "60-second ad, serious, climate change impact, target: eco-conscious consumers, platform: YouTube, style: Documentary"
```

### 4. Wes Anderson Style
```bash
python sora_workflow.py --brief "30-second ad, whimsical, coffee shop ritual, target: millennials, platform: Instagram, style: Wes Anderson"
```

## Brief Format Tips

Your brief should include:
- **Duration**: "15-second", "30s", "60 seconds"
- **Tone**: sarcastic, serious, playful, dramatic, casual
- **Message**: The core concept or pain point
- **Target**: Your audience (media buyers, millennials, etc.)
- **Platform**: TikTok, Instagram, YouTube, etc.
- **Style**: Wolf of Wall Street, TikTok UGC, Documentary, Wes Anderson, etc.

## Available Styles

- **Wolf of Wall Street**: High-energy, excessive, luxury, sarcastic confidence
- **TikTok UGC**: Authentic, casual, mobile-first, relatable
- **Documentary**: Real, observational, intimate, informative
- **Wes Anderson**: Symmetrical, whimsical, pastel, quirky
- **Apple Commercial**: Clean, minimal, premium, product-focused
- **Action Sports**: High-energy, dynamic, extreme angles, adrenaline

## Output Sections

Each shot includes:
- **SHOT**: Number and sequence
- **SUBJECT**: Who/what is in frame
- **SCENE**: Location and setting
- **VISUAL DETAILS**: Specific visual elements
- **ACTION & CAMERA**: Movement and camera work
- **CINEMATOGRAPHY**: Technical specs (lighting, lens, etc.)
- **AUDIO**: Dialogue, music, sound design
- **STYLE**: Overall aesthetic and references

## What the Workflow Does

1. **Parses** your brief to extract key information
2. **Identifies** any missing critical details
3. **Asks** clarifying questions if needed (in interactive mode)
4. **Loads** the appropriate style template
5. **Generates** a complete storyboard with proper shot count for duration
6. **Formats** output with all required Sora sections
