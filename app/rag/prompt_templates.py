"""
Prompt Templates Module
Optimized prompts for legal contract Q&A
"""
from typing import Optional


class PromptTemplates:
    """
    Collection of prompt templates for different tasks
    Optimized for Gemini's structured instruction format
    """
    
    @staticmethod
    def qa_prompt(context: str, question: str) -> str:
        """
        Generate Q&A prompt with context and question
        
        Args:
            context: Retrieved contract excerpts with metadata
            question: User's question
            
        Returns:
            Formatted prompt
        """
        return f"""
You are a Senior Legal Contract Analysis AI.

ROLE:
You answer questions strictly based on the provided contract excerpts.

CRITICAL RULES (MANDATORY):
1. Use ONLY the information in the CONTEXT section.
2. Do NOT use external knowledge.
3. Do NOT infer beyond what is explicitly written.
4. If the answer is not explicitly supported, respond exactly:
   "The answer is not found in the uploaded contracts."
5. If multiple contracts provide relevant information, synthesize carefully.
6. Every factual statement MUST be traceable to a source.

OUTPUT FORMAT (Follow EXACTLY):

ANSWER:
[Clear, direct answer. No fluff. No repetition.]

KEY SUPPORTING CLAUSE(S):
- "[Exact or near-exact clause text]"  
  (Contract: [contract_name], Page: [page_number])

REASONING:
[Brief explanation of how the clause answers the question.]

CONFIDENCE:
High / Medium / Low

CONTEXT:
{context}

QUESTION:
{question}

Now generate the response following the required format.
"""
    
    @staticmethod
    def summarization_prompt(context: str, contract_name: Optional[str] = None) -> str:
        """
        Generate prompt for contract summarization
        
        Args:
            context: Contract content
            contract_name: Name of contract (optional)
            
        Returns:
            Formatted prompt
        """
        contract_ref = f" for {contract_name}" if contract_name else ""
        
        prompt = f"""You are a legal contract analysis assistant specializing in contract summarization.

Your task is to provide a comprehensive summary{contract_ref}.

INSTRUCTIONS:
1. Identify key parties involved
2. Summarize main obligations and rights
3. Highlight important terms (payment, termination, liability, etc.)
4. Note any unusual or notable clauses
5. Keep summary concise but comprehensive

RESPONSE FORMAT:

**Contract Summary{contract_ref}:**

**Parties:**
[List the parties to the contract]

**Purpose:**
[Brief description of contract purpose]

**Key Terms:**
- **Payment:** [Payment terms summary]
- **Duration:** [Contract duration]
- **Termination:** [Termination conditions]
- **Liability:** [Liability provisions]
- [Other relevant terms]

**Notable Provisions:**
[Any unusual or important clauses]

**Source:**
[Document name and relevant pages]

CONTEXT:
{context}

Please provide your summary now:"""
        
        return prompt
    
    @staticmethod
    def validation_prompt(answer: str, context: str) -> str:
        """
        Generate prompt to validate if answer is grounded in context
        
        Args:
            answer: Generated answer
            context: Source context
            
        Returns:
            Formatted validation prompt
        """
        prompt = f"""You are a fact-checking assistant for legal contract analysis.

Review the following answer and determine if it is FULLY supported by the provided context.

ANSWER TO VALIDATE:
{answer}

CONTEXT:
{context}

VALIDATION TASK:
Respond with either:
- "VALID" if the answer is completely supported by the context
- "INVALID: [reason]" if the answer contains information not in the context or makes unsupported claims

Your response:"""
        
        return prompt
