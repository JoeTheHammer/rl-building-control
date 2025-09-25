import Headline from './headline.tsx'
import React from 'react'

interface CustomPageProps {
  children: React.ReactNode
  headline: string
}

const CustomPage: React.FC<CustomPageProps> = ({ children, headline }) => {
  return (
    <div className="p-5 pt-5 md:px-10 lg:px-80">
      <Headline text={headline} />
      {children}
    </div>
  )
}

export default CustomPage
