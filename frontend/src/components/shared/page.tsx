import React from 'react'

interface CustomPageProps {
  children: React.ReactNode
}

const CustomPage: React.FC<CustomPageProps> = ({ children }) => {
  return <div className="p-5 pt-5 md:px-10 lg:px-80">{children}</div>
}

export default CustomPage
