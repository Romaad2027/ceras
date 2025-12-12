import { JoinOrganization } from './JoinOrganization.jsx'

export const JoinPage = () => {
  return (
    <div className="bg-[var(--md-sys-color-surface-container-lowest)] border border-outline-variant rounded-lg p-6 shadow-md">
      <JoinOrganization
        onSuccess={(token, tokenType) => {
          if (token) localStorage.setItem('token', token)
          if (tokenType) localStorage.setItem('token_type', tokenType)
          window.location.href = '/'
        }}
      />
    </div>
  )
}


