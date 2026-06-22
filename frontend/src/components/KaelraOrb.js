import React from "react";

/**
 * The signature Kaelra presence. A living orb that reflects her state.
 * states: idle | thinking | listening | speaking | offline
 */
export function KaelraOrb({ size = 56, state = "idle", className = "" }) {
  return (
    <div
      className={`orb-wrap orb-state-${state} ${className}`}
      style={{ width: size, height: size }}
      aria-hidden="true"
      data-testid="kaelra-orb"
      data-state={state}
    >
      <span className="orb-ring" />
      <span className="orb-ring" style={{ animationDelay: "0.7s" }} />
      <div className="orb-core" style={{ width: size, height: size }} />
    </div>
  );
}

export const ORB_STATUS = {
  idle: "Kaelra is here",
  thinking: "Checking your day…",
  listening: "Listening…",
  speaking: "Explaining…",
  offline: "Sync paused",
};
