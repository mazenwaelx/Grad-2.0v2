import './EmptyState.css';

const SUGGESTIONS = [
  { icon: '⏱️', text: 'ما هي ساعات العمل القانونية في مصر؟' },
  { icon: '🏖️', text: 'كم يوم إجازة سنوية يحق لي؟' },
  { icon: '📋', text: 'ما هي حقوقي إذا أنهى صاحب العمل عقدي؟' },
  { icon: '💰', text: 'كيف يتم حساب الأجر الإضافي حسب القانون المصري؟' },
];

const CAPABILITIES = [
  { icon: '🤝', text: 'عقود العمل والحقوق' },
  { icon: '⏰', text: 'ساعات العمل والعمل الإضافي' },
  { icon: '💰', text: 'الأجور والتعويضات' },
  { icon: '🏖️', text: 'الإجازات والعطلات' },
  { icon: '⚠️', text: 'إنهاء العقد والنزاعات' },
  { icon: '🛡️', text: 'حماية العمال' },
];

const EmptyState = ({ onSuggestionClick }) => {
  return (
    <div className="empty-state">
      <div className="empty-state-icon">⚖️</div>
      <h3>استشير <span className="arabic">مساعدك القانوني المصري</span></h3>
      <p className="subtitle">مساعدك الموثوق في قانون العمل المصري</p>

      <div className="empty-state-content">
        <div className="capabilities-section">
          <h4>📚 <span>كيف يمكنني مساعدتك:</span></h4>
          <div className="capabilities-grid">
            {CAPABILITIES.map((cap, index) => (
              <div key={index} className="capability-item">
                {cap.text} {cap.icon}
              </div>
            ))}
          </div>
        </div>

        <div className="suggestions-section">
          <h4>💡 <span>جرب السؤال:</span></h4>
          <div className="suggestions-list">
            {SUGGESTIONS.map((suggestion, index) => (
              <button
                key={index}
                className="suggestion-btn"
                onClick={() => onSuggestionClick(suggestion.text)}
              >
                <span className="suggestion-icon">{suggestion.icon}</span>
                {suggestion.text}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default EmptyState;
