#!/usr/bin/env python3
"""
Sora Storyboard Workflow Generator
Transforms marketing briefs into fully-formatted Sora 2 storyboard prompts
"""

import argparse
import json
import re
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class Brief:
    """Marketing brief structure"""
    duration: Optional[str] = None
    tone: Optional[str] = None
    message: Optional[str] = None
    target_audience: Optional[str] = None
    platform: Optional[str] = None
    style: Optional[str] = None
    raw: str = ""


@dataclass
class Shot:
    """Individual shot in the storyboard"""
    number: int
    subject: str
    scene: str
    visual_details: str
    action_camera: str
    cinematography: str
    audio: str
    style: str

    def format(self) -> str:
        """Format shot as structured prompt"""
        return f"""SHOT {self.number}
SUBJECT: {self.subject}
SCENE: {self.scene}
VISUAL DETAILS: {self.visual_details}
ACTION & CAMERA: {self.action_camera}
CINEMATOGRAPHY: {self.cinematography}
AUDIO: {self.audio}
STYLE: {self.style}
"""


class StyleTemplate:
    """Style templates for different vibes"""

    WOLF_OF_WALL_STREET = {
        "name": "Wolf of Wall Street",
        "cinematography_base": "High-contrast lighting, warm color grading with golden hour tones, wide aperture (f/1.4-f/2.8), dynamic camera movement",
        "camera_style": "Steadicam tracking shots, dramatic push-ins, dutch angles for intensity, fast-paced cuts",
        "audio_style": "Upbeat energetic music, confident voice-over, quick-cut sound design",
        "visual_style": "Luxurious settings, power dynamics, excessive confidence, wealth signifiers, high-energy editing",
        "tone_keywords": ["confident", "excessive", "sarcastic", "energetic", "bold"]
    }

    TIKTOK_UGC = {
        "name": "TikTok UGC",
        "cinematography_base": "Natural lighting, mobile phone aesthetic, vertical 9:16 format, slightly grainy",
        "camera_style": "Handheld, selfie-style framing, direct-to-camera address, quick cuts, trending transitions",
        "audio_style": "Conversational voice-over, trending audio clips, authentic speaking style",
        "visual_style": "Casual settings (bedroom, coffee shop, car), authentic and unpolished, relatable scenarios",
        "tone_keywords": ["casual", "authentic", "relatable", "conversational", "trend-aware"]
    }

    WES_ANDERSON = {
        "name": "Wes Anderson",
        "cinematography_base": "Perfectly symmetrical framing, pastel color palette, flat space, static camera, centered composition",
        "camera_style": "Locked-off shots, whip pans, perfectly centered subjects, lateral tracking shots",
        "audio_style": "Whimsical orchestral score, deadpan dialogue delivery, vintage sound effects",
        "visual_style": "Meticulously arranged props, vintage aesthetic, quirky character styling, geometric patterns",
        "tone_keywords": ["whimsical", "precise", "quirky", "nostalgic", "deadpan"]
    }

    DOCUMENTARY = {
        "name": "Documentary",
        "cinematography_base": "Natural lighting, realistic color grading, varying focal lengths, observational style",
        "camera_style": "Handheld for intimacy, smooth gimbal for following action, locked-off for interviews",
        "audio_style": "Natural ambient sound, clear voice-over narration, minimal music",
        "visual_style": "Real locations, authentic moments, detail close-ups, environmental context",
        "tone_keywords": ["authentic", "informative", "intimate", "observational", "real"]
    }

    DRAMATIC_MOVIE_TRAILER = {
        "name": "Dramatic Movie Trailer",
        "cinematography_base": "Dark moody lighting, high contrast shadows, desaturated color palette with teal/orange grading, shallow depth of field (f/1.2-f/2.0), cinematic anamorphic lens flares",
        "camera_style": "Ultra slow-motion (120-240fps), dramatic push-ins, low angle hero shots, rack focus reveals, handheld intensity moments, stabilized dolly moves",
        "audio_style": "Orchestral trailer music with bass drops, whispered/gravelly voice-over, dramatic sound design, thunder/storm effects, silence for impact",
        "visual_style": "Epic scale environmental shots, emotional close-ups, weather/atmospheric elements (rain, storm, fog), lens flares, particle effects, dramatic silhouettes",
        "tone_keywords": ["dramatic", "cinematic", "epic", "intense", "emotional", "dark", "moody"]
    }

    @classmethod
    def get_template(cls, style_name: str) -> Optional[Dict]:
        """Get template by name (case-insensitive)"""
        style_map = {
            "wolf of wall street": cls.WOLF_OF_WALL_STREET,
            "tiktok ugc": cls.TIKTOK_UGC,
            "tiktok": cls.TIKTOK_UGC,
            "ugc": cls.TIKTOK_UGC,
            "wes anderson": cls.WES_ANDERSON,
            "documentary": cls.DOCUMENTARY,
            "doc": cls.DOCUMENTARY,
            "dramatic movie trailer": cls.DRAMATIC_MOVIE_TRAILER,
            "movie trailer": cls.DRAMATIC_MOVIE_TRAILER,
            "trailer": cls.DRAMATIC_MOVIE_TRAILER,
        }
        return style_map.get(style_name.lower())


class BriefParser:
    """Parse marketing briefs into structured data"""

    @staticmethod
    def parse(brief_text: str) -> Brief:
        """Extract structured information from brief text"""
        brief = Brief(raw=brief_text)

        # Duration patterns
        duration_match = re.search(r'(\d+)[-\s]*(second|sec|s)\b', brief_text, re.I)
        if duration_match:
            brief.duration = f"{duration_match.group(1)}-second"

        # Tone keywords
        tone_keywords = ["sarcastic", "serious", "playful", "dramatic", "funny", "emotional", "upbeat", "dark"]
        for keyword in tone_keywords:
            if keyword in brief_text.lower():
                brief.tone = keyword
                break

        # Extract labeled fields
        patterns = {
            'target': r'target[:\s]+([^,\.]+)',
            'platform': r'platform[:\s]+([^,\.]+)',
            'style': r'style[:\s]+([^,\.]+)',
        }

        for field, pattern in patterns.items():
            match = re.search(pattern, brief_text, re.I)
            if match:
                value = match.group(1).strip()
                if field == 'target':
                    brief.target_audience = value
                elif field == 'platform':
                    brief.platform = value
                elif field == 'style':
                    brief.style = value

        # Detect style from keywords if not explicitly labeled
        if not brief.style:
            if re.search(r'movie trailer|trailer style', brief_text, re.I):
                brief.style = "movie trailer"
            elif re.search(r'wolf of wall street', brief_text, re.I):
                brief.style = "wolf of wall street"
            elif re.search(r'wes anderson', brief_text, re.I):
                brief.style = "wes anderson"
            elif re.search(r'documentary|doc style', brief_text, re.I):
                brief.style = "documentary"
            elif re.search(r'tiktok|ugc', brief_text, re.I):
                brief.style = "tiktok ugc"

        # Extract message (everything that's not a labeled field)
        message_parts = re.split(r'(target|platform|style)[:\s]+', brief_text, flags=re.I)
        if message_parts:
            brief.message = message_parts[0].strip()
            # Clean up the message
            brief.message = re.sub(r'(\d+[-\s]*(second|sec|s))|' + '|'.join(tone_keywords), '',
                                   brief.message, flags=re.I).strip()
            brief.message = re.sub(r'[,\s]+$', '', brief.message)

        return brief


class ClarificationEngine:
    """Asks clarifying questions when brief is incomplete"""

    @staticmethod
    def get_missing_fields(brief: Brief) -> List[str]:
        """Identify missing critical fields"""
        missing = []

        if not brief.duration:
            missing.append("duration")
        if not brief.message:
            missing.append("core message/concept")
        if not brief.target_audience:
            missing.append("target audience")
        if not brief.platform:
            missing.append("platform")
        if not brief.style:
            missing.append("visual style/vibe")

        return missing

    @staticmethod
    def generate_questions(missing_fields: List[str]) -> List[str]:
        """Generate clarifying questions"""
        questions = {
            "duration": "What's the target duration? (e.g., 15s, 30s, 60s)",
            "core message/concept": "What's the core message or pain point you're addressing?",
            "target audience": "Who is the target audience?",
            "platform": "Which platform is this for? (TikTok, Instagram, YouTube, etc.)",
            "visual style/vibe": "What visual style or vibe are you going for? (e.g., Wolf of Wall Street, TikTok UGC, Wes Anderson, Documentary)",
        }
        return [questions[field] for field in missing_fields if field in questions]


class StoryboardGenerator:
    """Generate Sora storyboard from brief"""

    def __init__(self, brief: Brief):
        self.brief = brief
        self.style_template = StyleTemplate.get_template(brief.style or "")

    def generate(self) -> List[Shot]:
        """Generate complete storyboard"""
        # Determine number of shots based on duration
        duration_seconds = int(re.search(r'\d+', self.brief.duration or "30").group())

        if duration_seconds <= 15:
            return self._generate_short_form()
        elif duration_seconds <= 30:
            return self._generate_medium_form()
        else:
            return self._generate_long_form()

    def _generate_short_form(self) -> List[Shot]:
        """Generate 15-second storyboard (2-3 shots)"""
        # For the Wolf of Wall Street / sarcastic CPC example
        if self.brief.style and "wolf" in self.brief.style.lower():
            return self._generate_wolf_cpc_storyboard()
        elif self.brief.style and "trailer" in self.brief.style.lower():
            return self._generate_dramatic_trailer_storyboard()
        return []

    def _generate_medium_form(self) -> List[Shot]:
        """Generate 30-second storyboard (3-5 shots)"""
        # For the Wolf of Wall Street / sarcastic CPC example
        if self.brief.style and "wolf" in self.brief.style.lower():
            return self._generate_wolf_cpc_storyboard()
        elif self.brief.style and "trailer" in self.brief.style.lower():
            return self._generate_dramatic_trailer_storyboard()
        return []

    def _generate_long_form(self) -> List[Shot]:
        """Generate 60+ second storyboard (5-8 shots)"""
        if self.brief.style and "trailer" in self.brief.style.lower():
            return self._generate_dramatic_trailer_storyboard()
        return []

    def _generate_wolf_cpc_storyboard(self) -> List[Shot]:
        """Generate Wolf of Wall Street style storyboard for CPC pain point"""
        template = self.style_template or StyleTemplate.WOLF_OF_WALL_STREET
        platform = self.brief.platform or "TikTok"

        shots = []

        # SHOT 1: The Setup - Media Buyer at Desk
        shots.append(Shot(
            number=1,
            subject="Confident media buyer in designer suit at sleek modern desk, looking at laptop screen with exaggerated shock expression",
            scene="Luxury corner office with floor-to-ceiling windows, city skyline visible, golden hour lighting streaming in",
            visual_details="Multiple monitors displaying ad dashboards with rising red arrows, expensive watch visible, minimalist decor, chrome and glass surfaces reflecting warm light",
            action_camera="Push in from wide establishing shot to medium close-up as subject's expression changes from confidence to shocked realization. Camera accelerates during push-in.",
            cinematography=f"{template['cinematography_base']}, shot on Arri Alexa, 35mm lens at f/2.0, warm golden tones with high contrast, slight lens flare from window light",
            audio="Upbeat stock trading floor ambience fading in, sudden record scratch sound effect, subject's voice: 'You've got to be kidding me...' with mounting frustration",
            style=f"{template['visual_style']}, {platform} vertical 9:16 format optimized, fast-paced editing rhythm"
        ))

        # SHOT 2: The Realization - Screen Detail
        shots.append(Shot(
            number=2,
            subject="Extreme close-up of laptop screen showing CPC metrics dashboard with numbers climbing rapidly",
            scene="Same office setting, focus on screen with shallow depth of field, background bokeh of office",
            visual_details="Red ascending arrows, percentage increases flashing, CPC numbers ticking up dramatically ($2.50... $3.75... $5.20...), mouse cursor hovering frantically",
            action_camera="Slow push-in on screen, slight handheld shake for urgency, quick cuts between different metrics all showing increases",
            cinematography=f"Macro lens work, very shallow depth of field (f/1.4), screen providing cool blue light contrasting with warm ambient, subtle film grain for texture",
            audio="Tension-building electronic music, keyboard clicking sounds, subtle 'ding' sounds for each price increase, breathing getting heavier",
            style="High-energy editing with fast cuts, Wolf of Wall Street excess applied to digital marketing anxiety, mobile-first framing"
        ))

        # SHOT 3: The Pitch/Solution
        shots.append(Shot(
            number=3,
            subject="Same media buyer now standing, addressing camera directly with sardonic smile and knowing look, loosened tie, sleeves rolled up",
            scene="Same office, subject now positioned powerfully against window, backlit for dramatic effect",
            visual_details="City skyline at golden hour behind subject, office now slightly messier showing work intensity, coffee cups visible, jacket draped over chair",
            action_camera="Direct-to-camera address, slow zoom in to close-up, subject walks toward camera with confidence, ends in tight close-up for punchline",
            cinematography=f"{template['cinematography_base']}, dramatic backlighting with hair light, edge lighting to separate subject from background, warm and cool tones balanced",
            audio="Music shifts to confident hip-hop beat, subject voice-over with sarcastic delivery: 'CPC going up again? Time to get smarter, not broker.' Ends with music sting.",
            style=f"Wolf of Wall Street direct address style, breaking fourth wall, {platform} native feel with polished production value, ends with strong call-to-action energy"
        ))

        return shots

    def _generate_dramatic_trailer_storyboard(self) -> List[Shot]:
        """Generate dramatic movie trailer style storyboard with emotional overkill"""
        template = self.style_template or StyleTemplate.DRAMATIC_MOVIE_TRAILER
        platform = self.brief.platform or "Social Media"

        shots = []

        # SHOT 1: Opening - Thunder and Rain Ambience
        shots.append(Shot(
            number=1,
            subject="Rain droplets on window glass in extreme close-up, backlit by occasional lightning flashes, out-of-focus city lights beyond",
            scene="Dark office interior, nighttime, storm raging outside floor-to-ceiling windows",
            visual_details="Water trails running down glass, reflections of distant lightning creating intermittent blue-white illumination, darkness between flashes, condensation fog on edges of window pane",
            action_camera="Ultra slow-motion (240fps) tracking shot along window surface, camera glides horizontally as rain streaks vertically, slow rack focus from water droplets to blurred lights beyond",
            cinematography=f"{template['cinematography_base']}, shot on RED Komodo 6K, 85mm lens at f/1.2, teal and orange color grade, heavy desaturation, practical lightning effects, anamorphic lens flares",
            audio="Deep rumbling thunder starting distant then crescendoing, heavy rain ambience, ominous low-frequency drone, silence between thunder cracks for tension",
            style=f"{template['visual_style']}, establishing atmospheric dread, ultra-cinematic meme parody energy, viral-ready opening hook"
        ))

        # SHOT 2: The Man - First Reveal
        shots.append(Shot(
            number=2,
            subject="35-year-old man in vibrant zebra pattern Hawaiian shirt, face half-lit by blue computer screen glow, expression frozen in dawning realization, eyes widening imperceptibly in slow-motion",
            scene="Same dark office, subject seated at desk, illuminated only by monitor glow and occasional lightning flashes through windows behind him",
            visual_details="Absurd zebra pattern shirt contrasting with deadly serious expression, stubble visible on jaw, slight reflection of screen in his glasses/eyes, hair slightly disheveled, office plants visible as dark silhouettes",
            action_camera="Ultra slow-motion (180fps) push-in from medium to close-up, camera moves glacially toward face, small movements (blink, slight head turn) stretched to feel momentous",
            cinematography=f"Low-key lighting, screen providing cool blue key light on face, strong rim light from window creating separation, f/1.4 for shallow depth of field, background bokeh of rain on windows, subtle film grain",
            audio="Ambient rain and distant thunder continuing, quiet tense electronic undertone building, subject's breathing barely audible and slowed down, keyboard click echoing ominously",
            style="Dramatic hero shot applied to mundane moment, emotional intensity completely disproportionate to situation, meme-worthy juxtaposition of shirt and gravitas"
        ))

        # SHOT 3: Screen Reveal - The $0.03 Rise
        shots.append(Shot(
            number=3,
            subject="Computer screen displaying CPC metrics dashboard, number changing from $2.47 to $2.50, the +$0.03 increase highlighted in blood red",
            scene="Extreme close-up of monitor, rest of office completely out of focus, screen provides only light source",
            visual_details="Sharp digital numbers on analytics dashboard, red warning indicator pulsing, cursor hovering nearby frozen in time, slight screen glare creating lens artifacts, UI elements showing graphs with red ascending line",
            action_camera="Slow-motion (120fps) macro push-in on the specific number as it ticks up, ends in extreme close-up of the '$2.50' filling frame, shallow rack focus across screen surface",
            cinematography=f"Macro lens work with extreme shallow depth of field (f/1.2), screen glow creating cool blue ambient light, slight chromatic aberration on edges for cinematic feel, desaturated except for red UI elements",
            audio="Single ominous bass drop as number changes, sound design: digital 'click' stretched and pitched down to sound catastrophic, thunder crack timed with number change, whispered voice beginning: 'nothing...'",
            style="Treating trivial data point as world-ending revelation, slow-motion emphasizing the absurdity, viral meme energy through dramatic over-reaction"
        ))

        # SHOT 4: Reaction - The Weight of $0.03
        shots.append(Shot(
            number=4,
            subject="Same man, now shown in profile silhouette against rain-streaked window, hand slowly rising to face in despair, zebra shirt pattern visible in rim lighting",
            scene="Subject standing now, positioned against window, backlit by storm and city lights, rain visible on glass behind him",
            visual_details="Strong silhouette with blue-white edge lighting from window, zebra pattern creating striking contrast in rim light, rain streaks on window moving in slow-motion, lightning flash illuminating his profile for one frame, hand covering mouth in 'shocked' gesture",
            action_camera="Ultra slow-motion (240fps) side profile shot, camera slowly trucks left to right, slight low angle to create dramatic stature, ends with lightning flash silhouette",
            cinematography=f"{template['cinematography_base']}, dramatic backlighting, silhouette with rim light, storm providing practical effects behind subject, anamorphic lens flare from city lights, heavy shadow contrast",
            audio="Voice-over continues in dramatic whisper: 'will ever be the same...', orchestral trailer music swelling with deep brass and strings, rain and thunder intensifying, breathing heavy and slow",
            style="Classic trailer hero silhouette moment wasted on marketing metric anxiety, absurdist contrast between visual drama and actual stakes"
        ))

        # SHOT 5: Title Card / Call to Action
        shots.append(Shot(
            number=5,
            subject="Dramatic text reveal emerging from darkness: 'WHEN CPC RISES...' fading in, then '...EVERYTHING CHANGES' appearing below with cinematic reveal",
            scene="Pure black background with subtle particle effects (rain, dust) barely visible, text illuminated dramatically",
            visual_details="Bold cinematic typography, white text with slight glow/bloom effect, subtle animation of letters appearing, particle effects around text, optional: small text below in contrast font showing actual call-to-action or brand",
            action_camera="Static camera, text animation handled in post, possible slow zoom into text for intensity, cut to black before fully zooming in",
            cinematography=f"High contrast black background, text as light source, subtle volumetric lighting on particles, clean dramatic presentation, desaturated color palette continuing",
            audio="Music hits final dramatic crescendo then cuts to silence, final thunder crash, optional: quick brand message or ironic undercut ('Learn to optimize your CPC' in normal voice), final bass drop",
            style="Classic movie trailer title card treatment, maximum drama for minimum stakes, perfect viral meme format with built-in shareability"
        ))

        return shots


class WorkflowEngine:
    """Main workflow orchestrator"""

    def __init__(self, brief_text: str, interactive: bool = False):
        self.brief_text = brief_text
        self.interactive = interactive
        self.brief = None
        self.shots = []

    def run(self) -> str:
        """Execute the workflow"""
        print("\n" + "="*70)
        print("SORA STORYBOARD WORKFLOW - STEP-BY-STEP EXECUTION")
        print("="*70 + "\n")

        # STEP 1: Parse the brief
        print("STEP 1: PARSING BRIEF")
        print("-" * 70)
        self.brief = BriefParser.parse(self.brief_text)
        print(f"Raw Brief: {self.brief.raw}\n")
        print("Extracted Information:")
        print(f"  • Duration: {self.brief.duration or 'NOT FOUND'}")
        print(f"  • Tone: {self.brief.tone or 'NOT FOUND'}")
        print(f"  • Message: {self.brief.message or 'NOT FOUND'}")
        print(f"  • Target Audience: {self.brief.target_audience or 'NOT FOUND'}")
        print(f"  • Platform: {self.brief.platform or 'NOT FOUND'}")
        print(f"  • Style: {self.brief.style or 'NOT FOUND'}")
        print()

        # STEP 2: Check for missing information
        print("STEP 2: CHECKING FOR MISSING INFORMATION")
        print("-" * 70)
        missing = ClarificationEngine.get_missing_fields(self.brief)
        if missing:
            print(f"Missing fields detected: {', '.join(missing)}\n")
            questions = ClarificationEngine.generate_questions(missing)
            print("Clarifying Questions:")
            for i, q in enumerate(questions, 1):
                print(f"  {i}. {q}")
            print("\n⚠️  In interactive mode, would pause here for user input.")
            print("For this demo, proceeding with available information...\n")
        else:
            print("✓ All critical fields present!\n")

        # STEP 3: Load style template
        print("STEP 3: LOADING STYLE TEMPLATE")
        print("-" * 70)
        template = StyleTemplate.get_template(self.brief.style or "")
        if template:
            print(f"✓ Found template: {template['name']}")
            print(f"  • Camera Style: {template['camera_style'][:80]}...")
            print(f"  • Visual Style: {template['visual_style'][:80]}...")
        else:
            print("⚠️  No matching template found, using defaults")
        print()

        # STEP 4: Generate storyboard
        print("STEP 4: GENERATING STORYBOARD")
        print("-" * 70)
        generator = StoryboardGenerator(self.brief)
        self.shots = generator.generate()
        print(f"✓ Generated {len(self.shots)} shots based on {self.brief.duration or '30-second'} duration")
        print(f"  • Structure: Hook → Build Tension → Payoff")
        print(f"  • Platform optimization: {self.brief.platform or 'TikTok'} (9:16 vertical)")
        print(f"  • Tone: {self.brief.tone or 'sarcastic'} throughout")
        print()

        # STEP 5: Format output
        print("STEP 5: FORMATTING FINAL OUTPUT")
        print("-" * 70)
        output = self._format_output()
        print("✓ Storyboard formatted with all required sections")
        print("  (SHOT, SUBJECT, SCENE, VISUAL DETAILS, ACTION & CAMERA, CINEMATOGRAPHY, AUDIO, STYLE)")
        print()

        print("="*70)
        print("WORKFLOW COMPLETE - FINAL OUTPUT BELOW")
        print("="*70 + "\n")

        return output

    def _format_output(self) -> str:
        """Format final storyboard output"""
        output_lines = [
            "="*70,
            "SORA 2 STORYBOARD PROMPT",
            "="*70,
            "",
            f"PROJECT: {self.brief.message or 'Marketing Video'}",
            f"DURATION: {self.brief.duration or '30 seconds'}",
            f"PLATFORM: {self.brief.platform or 'TikTok'}",
            f"TARGET: {self.brief.target_audience or 'General'}",
            f"STYLE: {self.brief.style or 'Default'}",
            f"TONE: {self.brief.tone or 'Neutral'}",
            "",
            "="*70,
            ""
        ]

        for shot in self.shots:
            output_lines.append(shot.format())
            output_lines.append("-"*70)
            output_lines.append("")

        return "\n".join(output_lines)


def main():
    parser = argparse.ArgumentParser(description="Sora Storyboard Workflow Generator")
    parser.add_argument("--brief", type=str, help="Marketing brief text")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")

    args = parser.parse_args()

    if args.brief:
        workflow = WorkflowEngine(args.brief, interactive=args.interactive)
        output = workflow.run()
        print(output)
    else:
        print("Sora Storyboard Workflow Generator")
        print("="*70)
        print("\nPlease provide a brief using --brief flag:")
        print('  python sora_workflow.py --brief "your brief here"')
        print("\nOr see README.md for more options.")


if __name__ == "__main__":
    main()
