import React from "react";

export default function SuggestionChips({ suggestions, onClickSuggestion }) {
  return (
    <div className="blb-suggestions">
      {suggestions.map((s, idx) => (
        <button
          key={idx}
          type="button"
          className="blb-suggestion-chip"
          onClick={() => onClickSuggestion(s)}
        >
          {s}
        </button>
      ))}
    </div>
  );
}
