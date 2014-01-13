\NeedsTeXFormat{LaTeX2e}[1994/12/01]
\ProvidesClass{report}[2001/05/28 Document Report]

\LoadClass{article}
\RequirePackage[utf8]{inputenc}
\RequirePackage[T1]{fontenc}
\RequirePackage{graphicx}
\RequirePackage{fancyhdr}

\renewcommand{\headheight}{0.6in}
\setlength{\headwidth}{\textwidth}
\pagestyle{fancy}
\fancyhf{}


\newcommand{\logo}[1]{
\fancyhead[L]{ #1 }
}

\newcommand{\name}[1]{
\fancyhead[R]{ #1 }
}


