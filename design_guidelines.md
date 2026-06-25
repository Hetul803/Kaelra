{
  "design_system_name": "Kaelra Home — The Entity Presence (HOME-only)",
  "scope": {
    "applies_to": ["/ (Home route only)"],
    "do_not_change": [
      "Existing routes/components outside Home",
      "Existing dark-glass tokens in index.css",
      "No purple anywhere"
    ]
  },
  "brand_attributes": {
    "tone": ["cinematic", "omniscient", "calm power", "trustworthy", "quietly proactive"],
    "copy_voice": {
      "rules": [
        "Short, declarative sentences.",
        "Avoid hype; imply capability through specificity.",
        "Use present-continuous for ambient status (Watching, Learning, Syncing).",
        "Use second-person for nudges (I can connect Google to start learning)."
      ],
      "example_lines": [
        "I’m here.",
        "Say it. I’ll handle the rest.",
        "Watching your inbox · Learning · Standing by",
        "I flagged 2 emails that need a reply. Want me to draft them?"
      ]
    }
  },
  "typography": {
    "fonts": {
      "heading": "Space Grotesk (existing)",
      "body": "Figtree (existing)",
      "mono": "IBM Plex Mono (existing)"
    },
    "scale_tailwind": {
      "h1": "text-4xl sm:text-5xl lg:text-6xl font-semibold tracking-tight",
      "h2": "text-base md:text-lg text-muted-foreground",
      "section_title": "text-sm font-semibold tracking-tight",
      "kicker": "kaelra-kicker (existing class)",
      "body": "text-sm md:text-base",
      "meta": "font-mono-k text-xs text-muted-foreground"
    },
    "usage": {
      "home_hero": {
        "headline": "Space Grotesk; keep to 6–10 words max",
        "subhead": "Figtree; 1–2 lines; no more than text-lg on md+"
      },
      "feed_items": {
        "title": "Figtree 500",
        "source": "IBM Plex Mono"
      }
    }
  },
  "color_system": {
    "note": "Keep existing dark-first teal/amber/cyan tokens. Add HOME-only semantic aliases via CSS variables on a Home wrapper (do not change :root).",
    "home_wrapper_tokens": {
      "apply_on": "Home root container (e.g., <main data-testid=\"home-root\">)",
      "css_custom_properties": {
        "--home-surface": "rgba(255,255,255,0.06)",
        "--home-surface-2": "rgba(255,255,255,0.09)",
        "--home-stroke": "rgba(255,255,255,0.10)",
        "--home-glow-teal": "rgba(45,212,191,0.22)",
        "--home-glow-cyan": "rgba(56,189,248,0.18)",
        "--home-glow-amber": "rgba(245,158,11,0.14)",
        "--home-danger": "hsl(var(--destructive))",
        "--home-success": "hsl(156 62% 42%)",
        "--home-warning": "hsl(var(--accent))"
      }
    },
    "component_semantics": {
      "status_line": {
        "bg": "rgba(255,255,255,0.04)",
        "text": "hsl(var(--muted-foreground))",
        "active_dot": "hsl(var(--primary))",
        "alert_dot": "hsl(var(--accent))"
      },
      "composer": {
        "bg": "var(--home-surface)",
        "border": "var(--home-stroke)",
        "focus_ring": "var(--kaelra-focus)"
      },
      "memory_stream": {
        "learned_badge": "use Badge with variant=secondary + left border accent teal",
        "source_chip": "mono chip with subtle cyan stroke"
      }
    }
  },
  "layout": {
    "mobile_first_principle": "Conversation composer is always visible above the fold on mobile.",
    "grid": {
      "container": "max-w-6xl mx-auto px-4 sm:px-6",
      "desktop_grid": "lg:grid lg:grid-cols-12 lg:gap-6",
      "left_col": "lg:col-span-7",
      "right_col": "lg:col-span-5"
    },
    "home_structure": [
      {
        "region": "Ambient Status Line (sticky)",
        "purpose": "Always-on presence + system truth",
        "placement": "Top of Home content area; sticky within scroll container",
        "height": "40–44px",
        "data_testid": "home-ambient-status"
      },
      {
        "region": "Hero: Kaelra Orb + Greeting",
        "purpose": "Cinematic presence; establishes ‘Entity’",
        "placement": "Above fold; orb left on desktop, centered on mobile",
        "data_testid": "home-hero"
      },
      {
        "region": "Always-present Composer",
        "purpose": "Conversation-first input + voice controls",
        "placement": "Immediately under hero; sticky on desktop right rail",
        "data_testid": "home-composer"
      },
      {
        "region": "Proactive Feed",
        "purpose": "Actionable intelligence (emails/events/files)",
        "placement": "Left column; scrollable list",
        "data_testid": "home-proactive-feed"
      },
      {
        "region": "What I’ve Learned (Continuous Memory)",
        "purpose": "Shows evolving memory; builds trust",
        "placement": "Right column under composer (desktop) / below feed (mobile)",
        "data_testid": "home-learned-stream"
      }
    ],
    "spacing": {
      "section_gap": "space-y-6 md:space-y-8",
      "card_padding": "p-4 md:p-5",
      "list_item_gap": "gap-3",
      "touch_targets": "min-h-[44px]"
    }
  },
  "components": {
    "shadcn_primary": {
      "card": "/app/frontend/src/components/ui/card.jsx",
      "button": "/app/frontend/src/components/ui/button.jsx",
      "badge": "/app/frontend/src/components/ui/badge.jsx",
      "tabs": "/app/frontend/src/components/ui/tabs.jsx",
      "scroll_area": "/app/frontend/src/components/ui/scroll-area.jsx",
      "separator": "/app/frontend/src/components/ui/separator.jsx",
      "tooltip": "/app/frontend/src/components/ui/tooltip.jsx",
      "sheet": "/app/frontend/src/components/ui/sheet.jsx",
      "skeleton": "/app/frontend/src/components/ui/skeleton.jsx",
      "sonner": "/app/frontend/src/components/ui/sonner.jsx"
    },
    "existing_app_components_to_reuse": {
      "kaelra_orb": "/app/frontend/src/components/KaelraOrb.js",
      "kaelra_speaks_modal": "Existing KaelraSpeaks modal (do not redesign globally)",
      "bits": "SectionTitle / StatusPill / LoadingState (existing)",
      "app_shell": "AppShell (existing)"
    },
    "home_only_new_components_suggested_js": [
      {
        "name": "AmbientStatusLine",
        "purpose": "Sticky presence line with live dots + rotating status text",
        "data_testid": "home-ambient-status",
        "notes": "Pure presentational; receives {status, lastSyncAt, learnedCount, watchingTargets[]}"
      },
      {
        "name": "ConversationComposer",
        "purpose": "Text input + voice listen/speak controls + quick intents",
        "data_testid": "home-composer",
        "notes": "Uses useVoice(); must not break /talk route"
      },
      {
        "name": "ProactiveFeedList",
        "purpose": "Render /api/feed items with priority + action affordances",
        "data_testid": "home-proactive-feed"
      },
      {
        "name": "LearnedStream",
        "purpose": "Continuous memory surface filtered by learned:true",
        "data_testid": "home-learned-stream"
      }
    ]
  },
  "home_hero_orb": {
    "visual": {
      "orb_size": {
        "mobile": "w-[180px] h-[180px]",
        "desktop": "w-[240px] h-[240px]"
      },
      "surround": "Add subtle HUD rings using pseudo-elements or extra divs; keep gradients decorative and small.",
      "background": "Use existing .kaelra-app-bg; add a small radial glow behind orb only (max ~280px)."
    },
    "states": {
      "idle": "orb-breathe (existing)",
      "listening": "orb-ring ripple + slightly increased glow teal",
      "thinking": "faster breathe + faint cyan shimmer",
      "speaking": "warm amber bias in inner glow",
      "offline": "desaturate + reduce opacity"
    },
    "audio_reactive_feel": {
      "no_heavy_canvas": "Prefer CSS + framer-motion scale/opacity only.",
      "implementation_hint": "Map mic level (0..1) to orb scale 1..1.06 and ring opacity 0.2..0.6; clamp; animate with spring.",
      "prefers_reduced_motion": "Disable reactive scaling; keep static orb with state label."
    }
  },
  "conversation_composer": {
    "placement": {
      "mobile": "Inline under hero; full width",
      "desktop": "Sticky in right column: `lg:sticky lg:top-16` (below ambient status)"
    },
    "structure": {
      "container_classes": "glass p-4 md:p-5",
      "header": {
        "left": "‘Talk to Kaelra’ label + small status dot",
        "right": "Push-enable nudge button (ghost)"
      },
      "input": {
        "component": "Textarea (shadcn) or Input + autosize; prefer Textarea for multi-line",
        "classes": "min-h-[52px] resize-none bg-transparent border border-[color:var(--home-stroke)] focus-visible:ring-0 focus:outline-none rounded-[var(--radius)] px-3 py-3",
        "placeholder": "Ask me to triage, schedule, draft, or find anything…",
        "data_testid": "home-composer-textarea"
      },
      "controls": [
        {
          "name": "Listen",
          "icon": "lucide-react Mic",
          "variant": "secondary",
          "classes": "min-h-[44px]",
          "data_testid": "home-composer-listen-button"
        },
        {
          "name": "Send",
          "icon": "lucide-react ArrowUpRight",
          "variant": "default",
          "classes": "min-h-[44px]",
          "data_testid": "home-composer-send-button"
        },
        {
          "name": "Stop",
          "icon": "lucide-react Square",
          "variant": "ghost",
          "data_testid": "home-composer-stop-button"
        }
      ],
      "quick_intents": {
        "component": "Badge as clickable chips (or Button variant=ghost size=sm)",
        "items": [
          "What needs my attention today?",
          "Draft replies to urgent emails",
          "Summarize my next meeting",
          "What did you learn since yesterday?"
        ],
        "chip_classes": "cursor-pointer select-none hover:bg-white/10",
        "data_testid_prefix": "home-composer-intent"
      }
    },
    "micro_interactions": {
      "focus": "On focus, show subtle teal ring (use existing --kaelra-focus).",
      "send": "Button press scale 0.98 (framer-motion) + sonner toast on error.",
      "listening": "Composer header dot pulses (opacity only)."
    }
  },
  "ambient_status_line": {
    "visual": {
      "container_classes": "sticky top-0 z-20 backdrop-blur-md bg-black/20 border-b border-white/10",
      "inner_classes": "max-w-6xl mx-auto px-4 sm:px-6 h-11 flex items-center justify-between",
      "left": "Status dot + rotating phrase",
      "right": "Last sync + small action (Connect Google / Enable push)"
    },
    "content_model": {
      "phrases_rotation": [
        "Watching your inbox",
        "Indexing calendar",
        "Learning from Drive",
        "Standing by"
      ],
      "format": "Phrase · Learned {n} · Synced {time}"
    },
    "motion": {
      "dot": "Ping ring every 2.4s (opacity/scale only)",
      "text": "Crossfade between phrases every 6–8s (framer-motion AnimatePresence)"
    },
    "data_testids": {
      "root": "home-ambient-status",
      "phrase": "home-ambient-status-phrase",
      "sync": "home-ambient-status-sync"
    }
  },
  "proactive_feed": {
    "data_source": "GET /api/feed",
    "layout": {
      "container": "glass p-4 md:p-5",
      "header": "SectionTitle: ‘Priority feed’ + Tabs (All / Email / Calendar / Files)",
      "list": "ScrollArea with max-h on desktop (e.g., lg:max-h-[520px])"
    },
    "feed_item_card": {
      "pattern": "Left: icon + title; Right: time + action button",
      "classes": "rounded-[var(--kaelra-radius-card)] border border-white/10 bg-white/5 hover:bg-white/7",
      "states": {
        "unread": "left border teal 2px",
        "urgent": "left border amber 2px + subtle amber dot",
        "handled": "reduced opacity 0.75"
      },
      "actions": [
        "Open",
        "Draft reply",
        "Schedule",
        "Snooze"
      ],
      "data_testid_prefix": "home-feed-item"
    },
    "empty_state": {
      "tone": "warm, premium, inviting",
      "copy": {
        "title": "Nothing urgent right now.",
        "body": "Connect Google and I’ll start learning your patterns—email, calendar, and files.",
        "cta": "Connect Google"
      },
      "cta_data_testid": "home-empty-connect-google"
    }
  },
  "learned_stream": {
    "data_source": "memories with learned:true (existing backend flag)",
    "layout": {
      "container": "glass p-4 md:p-5",
      "header": "SectionTitle: ‘What I’ve learned’ + small ‘View Memory’ link",
      "list": "Vertical timeline feel (left rail line + nodes)"
    },
    "item_design": {
      "node": "6px dot teal; amber if ‘important’",
      "card": "bg-white/5 border-white/10 rounded-xl p-3",
      "meta": "mono: source (email/drive) + timestamp",
      "content": "1–2 lines summary; expand via Collapsible"
    },
    "interactions": {
      "expand": "Collapsible with height animation (framer-motion optional; else CSS)",
      "trust": "Show ‘Why I learned this’ tooltip (Tooltip component)"
    },
    "data_testid_prefix": "home-learned-item"
  },
  "motion_system": {
    "library": "framer-motion (available)",
    "principles": [
      "Animate only transform and opacity.",
      "Use slow, deliberate easing (cinematic).",
      "Respect prefers-reduced-motion: reduce."
    ],
    "durations": {
      "micro": "120–180ms",
      "panel": "220–320ms",
      "hero": "600–900ms"
    },
    "easing": {
      "standard": "[0.22, 1, 0.36, 1]",
      "soft": "[0.16, 1, 0.3, 1]"
    },
    "patterns": {
      "fade_up": "Use existing .kaelra-fade-up for initial mount of sections",
      "hover_lift": "hover:translate-y-[-2px] + shadow increase (no transition:all)",
      "orb_react": "spring scale with low bounce"
    }
  },
  "accessibility": {
    "focus": "Visible focus rings on all interactive elements; use --kaelra-focus.",
    "contrast": "Ensure text-muted-foreground is not used for primary content.",
    "touch": "44px min height for buttons and tappable list rows.",
    "reduced_motion": "Disable orb animations + phrase crossfade; keep static status text.",
    "aria": {
      "voice_controls": "Add aria-pressed for listening state; aria-live polite for status line updates."
    }
  },
  "data_testid_rules": {
    "mandatory": "All interactive and key informational elements must include data-testid.",
    "naming": "kebab-case describing role (not appearance)",
    "examples": [
      "data-testid=\"home-composer-send-button\"",
      "data-testid=\"home-feed-item-0-open-button\"",
      "data-testid=\"home-learned-item-3-source\"",
      "data-testid=\"home-ambient-status-phrase\""
    ]
  },
  "libraries_optional": {
    "recommended": [
      {
        "name": "react-three-fiber",
        "use_case": "Optional future upgrade for true 3D orb; NOT required for this iteration.",
        "install": "npm i three @react-three/fiber @react-three/drei",
        "guardrails": "Only if performance budget allows; keep fallback to existing KaelraOrb.js"
      }
    ],
    "do_not_add": ["heavy particle canvases on Home by default"]
  },
  "image_urls": {
    "ambient_background_overlays": [
      {
        "url": "https://images.unsplash.com/photo-1557688543-4e2f83d6796b?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzh8MHwxfHNlYXJjaHwyfHxkYXJrJTIwYWJzdHJhY3QlMjBkYXRhJTIwcGFydGljbGVzJTIwdGVhbCUyMGdsb3d8ZW58MHx8fHRlYWx8MTc4MjM1MjMyNXww&ixlib=rb-4.1.0&q=85",
        "category": "decorative",
        "description": "Optional subtle noise/particle overlay for hero only (opacity 0.06–0.10)."
      },
      {
        "url": "https://images.pexels.com/photos/2020309/pexels-photo-2020309.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
        "category": "decorative",
        "description": "Bokeh texture for small masked overlay behind orb (max 280px)."
      }
    ],
    "amber_accent_texture": [
      {
        "url": "https://images.pexels.com/photos/35990758/pexels-photo-35990758.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
        "category": "decorative",
        "description": "Warm amber spheres texture for tiny accent in ‘speaking’ state background (very low opacity)."
      }
    ]
  },
  "instructions_to_main_agent": {
    "home_page_composition": [
      "Keep AppShell and global background (.kaelra-app-bg).",
      "Implement Home layout with a sticky AmbientStatusLine at top of Home content.",
      "Hero: left side KaelraOrb + greeting; right side ConversationComposer (sticky on desktop).",
      "Below: ProactiveFeedList (left) and LearnedStream (right).",
      "Use ScrollArea for feed and learned stream on desktop to keep composer visible.",
      "Do not introduce new global CSS tokens; add HOME-only wrapper classes or inline Tailwind utilities.",
      "Ensure every button/input/link/list row has data-testid."
    ],
    "copy_blocks": {
      "hero_headline": "Kaelra is present.",
      "hero_subhead": "Tell me what you want done. I’ll watch your accounts, learn your patterns, and keep you ahead.",
      "composer_hint": "Try: ‘Summarize my inbox and draft replies to anything urgent.’"
    },
    "do_not_break": [
      "Existing KaelraOrb CSS animations (only extend with state classes)",
      "Existing /talk flow",
      "Existing shadcn component patterns"
    ]
  },
  "general_ui_ux_design_guidelines_appendix": "<General UI UX Design Guidelines>  \n    - You must **not** apply universal transition. Eg: `transition: all`. This results in breaking transforms. Always add transitions for specific interactive elements like button, input excluding transforms\n    - You must **not** center align the app container, ie do not add `.App { text-align: center; }` in the css file. This disrupts the human natural reading flow of text\n   - NEVER: use AI assistant Emoji characters like`🤖🧠💭💡🔮🎯📚🎭🎬🎪🎉🎊🎁🎀🎂🍰🎈🎨🎰💰💵💳🏦💎🪙💸🤑📊📈📉💹🔢🏆🥇 etc for icons. Always use **FontAwesome cdn** or **lucid-react** library already installed in the package.json\n\n **GRADIENT RESTRICTION RULE**\nNEVER use dark/saturated gradient combos (e.g., purple/pink) on any UI element.  Prohibited gradients: blue-500 to purple 600, purple 500 to pink-500, green-500 to blue-500, red to pink etc\nNEVER use dark gradients for logo, testimonial, footer etc\nNEVER let gradients cover more than 20% of the viewport.\nNEVER apply gradients to text-heavy content or reading areas.\nNEVER use gradients on small UI elements (<100px width).\nNEVER stack multiple gradient layers in the same viewport.\n\n**ENFORCEMENT RULE:**\n    • Id gradient area exceeds 20% of viewport OR affects readability, **THEN** use solid colors\n\n**How and where to use:**\n   • Section backgrounds (not content backgrounds)\n   • Hero section header content. Eg: dark to light to dark color\n   • Decorative overlays and accent elements only\n   • Hero section with 2-3 mild color\n   • Gradients creation can be done for any angle say horizontal, vertical or diagonal\n\n- For AI chat, voice application, **do not use purple color. Use color like light green, ocean blue, peach orange etc**\n\n</Font Guidelines>\n\n- Every interaction needs micro-animations - hover states, transitions, parallax effects, and entrance animations. Static = dead. \n   \n- Use 2-3x more spacing than feels comfortable. Cramped designs look cheap.\n\n- Subtle grain textures, noise overlays, custom cursors, selection states, and loading animations: separates good from extraordinary.\n   \n- Before generating UI, infer the visual style from the problem statement (palette, contrast, mood, motion) and immediately instantiate it by setting global design tokens (primary, secondary/accent, background, foreground, ring, state colors), rather than relying on any library defaults. Don't make the background dark as a default step, always understand problem first and define colors accordingly\n    Eg: - if it implies playful/energetic, choose a colorful scheme\n           - if it implies monochrome/minimal, choose a black–white/neutral scheme\n\n**Component Reuse:**\n\t- Prioritize using pre-existing components from src/components/ui when applicable\n\t- Create new components that match the style and conventions of existing components when needed\n\t- Examine existing components to understand the project's component patterns before creating new ones\n\n**IMPORTANT**: Do not use HTML based component like dropdown, calendar, toast etc. You **MUST** always use `/app/frontend/src/components/ui/ ` only as a primary components as these are modern and stylish component\n\n**Best Practices:**\n\t- Use Shadcn/UI as the primary component library for consistency and accessibility\n\t- Import path: ./components/[component-name]\n\n**Export Conventions:**\n\t- Components MUST use named exports (export const ComponentName = ...)\n\t- Pages MUST use default exports (export default function PageName() {...})\n\n**Toasts:**\n  - Use `sonner` for toasts\"\n  - Sonner component are located in `/app/src/components/ui/sonner.tsx`\n\nUse 2–4 color gradients, subtle textures/noise overlays, or CSS-based noise to avoid flat visuals.\n</General UI UX Design Guidelines>"
}
