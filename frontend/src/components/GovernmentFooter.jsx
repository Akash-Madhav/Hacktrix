import React from 'react';
import { ShieldCheck } from 'lucide-react';

export default function GovernmentFooter({ activeTab }) {
  const isRecordsTab = activeTab === 'records';

  return (
    <footer className="gov-footer">
      <div>
        <strong>NIRIKSHA</strong> | AICTE Approval Monitoring
      </div>

      <div className="gov-footer-motto">
        AI advises. Rules decide. Humans approve.
      </div>

      <div className="gov-footer-status">
        <ShieldCheck size={16} color="#168653" />
        <span>
          {isRecordsTab ? 'Secure institutional records' : 'Audit reference available'}
        </span>
        {!isRecordsTab && <span>&bull; Last updated: 30 Oct 2026, 03:00 PM</span>}
      </div>
    </footer>
  );
}
