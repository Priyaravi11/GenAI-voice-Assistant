const languages = [
  "English (US)",
  "Hindi (hi)",
  "Tamil (ta)",
  "Telugu (te)",
  "Kannada (kn)",
  "Spanish (es)",
];

type LanguageSelectorProps = {
  value: string;
  onChange: (language: string) => void;
};

function LanguageSelector({ value, onChange }: LanguageSelectorProps) {
  return (
    <label className="field-control">
      Voice Language
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        {languages.map((language) => (
          <option key={language}>{language}</option>
        ))}
      </select>
    </label>
  );
}

export default LanguageSelector;
