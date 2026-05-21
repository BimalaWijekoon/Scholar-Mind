"""
Research Question Generator - Generate research questions from documents

This module analyzes documents and the knowledge graph to suggest:
- Research questions based on identified gaps
- Follow-up questions for exploration
- Comparative research questions
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import random


class QuestionType(str, Enum):
    """Types of research questions."""
    EXPLORATORY = "exploratory"  # What/how questions
    COMPARATIVE = "comparative"  # Comparing methods/approaches
    CAUSAL = "causal"  # Why/cause-effect questions
    GAP = "gap"  # Addressing research gaps
    EXTENSION = "extension"  # Extending existing work
    APPLICATION = "application"  # Applying methods to new domains
    EVALUATION = "evaluation"  # Evaluating methods/claims


@dataclass
class ResearchQuestion:
    """Represents a generated research question."""
    question: str
    question_type: QuestionType
    relevance_score: float
    source_concepts: List[str]
    rationale: str
    suggested_methods: List[str]
    related_documents: List[str]


class ResearchQuestionGenerator:
    """
    Generate research questions from documents and knowledge graph.
    
    Analyzes entities, relationships, and gaps in the literature
    to suggest meaningful research questions.
    """
    
    def __init__(self, llm=None, graph_service=None):
        """
        Initialize the generator.
        
        Args:
            llm: Language model for question generation
            graph_service: Graph service for relationship analysis
        """
        self.llm = llm
        self.graph_service = graph_service
        
        # Question templates
        self.templates = self._define_templates()
    
    def _define_templates(self) -> Dict[QuestionType, List[str]]:
        """Define question templates for each type."""
        return {
            QuestionType.EXPLORATORY: [
                "What are the key factors that influence {concept} in {domain}?",
                "How does {method} work in the context of {task}?",
                "What are the main characteristics of {concept}?",
                "How can {concept1} be applied to improve {concept2}?",
                "What role does {concept} play in {domain}?",
            ],
            QuestionType.COMPARATIVE: [
                "How does {method1} compare to {method2} for {task}?",
                "What are the relative advantages of {approach1} vs {approach2}?",
                "Under what conditions does {method1} outperform {method2}?",
                "How do different {concept_type} approaches affect {metric}?",
                "What are the trade-offs between {method1} and {method2}?",
            ],
            QuestionType.CAUSAL: [
                "Why does {method} perform better on {dataset}?",
                "What causes the improvement in {metric} when using {technique}?",
                "How does {factor} affect the performance of {method}?",
                "What mechanisms explain the relationship between {concept1} and {concept2}?",
                "Why do {phenomenon} occur in {context}?",
            ],
            QuestionType.GAP: [
                "How can {method} be extended to handle {challenge}?",
                "What are the unexplored applications of {concept} in {domain}?",
                "How can we address the limitation of {method} regarding {issue}?",
                "What is missing in current approaches to {task}?",
                "How can {concept} be improved for {use_case}?",
            ],
            QuestionType.EXTENSION: [
                "Can {method} be adapted for {new_domain}?",
                "How would {approach} perform on {different_task}?",
                "What modifications to {method} would improve {aspect}?",
                "Can the success of {method} on {task1} transfer to {task2}?",
                "How can {technique} be scaled for {larger_problem}?",
            ],
            QuestionType.APPLICATION: [
                "How can {method} be applied to {practical_domain}?",
                "What are the real-world applications of {concept}?",
                "How would {approach} perform in {industry} settings?",
                "Can {technique} be used for {application_area}?",
                "What are the implications of {finding} for {field}?",
            ],
            QuestionType.EVALUATION: [
                "How should {method} be evaluated for {task}?",
                "What metrics best capture the performance of {approach}?",
                "How robust is {method} to {variation}?",
                "What are the failure cases of {approach}?",
                "How generalizable are the results of {method}?",
            ],
        }
    
    async def generate(
        self,
        document_id: Optional[str] = None,
        concepts: Optional[List[str]] = None,
        question_types: Optional[List[QuestionType]] = None,
        num_questions: int = 10,
    ) -> List[ResearchQuestion]:
        """
        Generate research questions.
        
        Args:
            document_id: Source document ID (optional)
            concepts: List of concepts to focus on
            question_types: Types of questions to generate
            num_questions: Number of questions to generate
            
        Returns:
            List of ResearchQuestion objects
        """
        question_types = question_types or list(QuestionType)
        
        # Gather concepts from document if provided
        if document_id and self.graph_service:
            doc_concepts = await self._get_document_concepts(document_id)
            concepts = list(set((concepts or []) + doc_concepts))
        
        concepts = concepts or ["machine learning", "deep learning", "neural networks"]
        
        # Generate questions using templates
        questions = []
        
        for q_type in question_types:
            type_questions = await self._generate_type_questions(
                q_type, concepts, num_questions // len(question_types) + 1
            )
            questions.extend(type_questions)
        
        # If LLM is available, enhance questions
        if self.llm:
            questions = await self._enhance_with_llm(questions, concepts)
        
        # Score and rank questions
        scored_questions = self._score_questions(questions, concepts)
        scored_questions.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return scored_questions[:num_questions]
    
    async def _get_document_concepts(self, document_id: str) -> List[str]:
        """Extract key concepts from a document."""
        if not self.graph_service:
            return []
        
        try:
            entities = await self.graph_service.get_document_entities(document_id)
            return [e.get('label', e.get('text', '')) for e in entities[:20]]
        except Exception:
            return []
    
    async def _generate_type_questions(
        self,
        question_type: QuestionType,
        concepts: List[str],
        num_questions: int,
    ) -> List[ResearchQuestion]:
        """Generate questions of a specific type."""
        templates = self.templates.get(question_type, [])
        questions = []
        
        for _ in range(num_questions):
            if not templates:
                continue
            
            template = random.choice(templates)
            
            # Fill template with concepts
            filled_question = self._fill_template(template, concepts)
            
            if filled_question:
                questions.append(ResearchQuestion(
                    question=filled_question,
                    question_type=question_type,
                    relevance_score=0.5,  # Will be scored later
                    source_concepts=self._extract_used_concepts(filled_question, concepts),
                    rationale=self._generate_rationale(question_type),
                    suggested_methods=self._suggest_methods(question_type, concepts),
                    related_documents=[],
                ))
        
        return questions
    
    def _fill_template(self, template: str, concepts: List[str]) -> Optional[str]:
        """Fill a template with concepts."""
        import re
        
        # Find all placeholders
        placeholders = re.findall(r'\{(\w+)\}', template)
        
        if not placeholders or len(concepts) < len(set(placeholders)):
            # Use default fillers
            defaults = {
                'concept': 'neural networks',
                'concept1': 'transformers',
                'concept2': 'attention mechanisms',
                'method': 'deep learning',
                'method1': 'BERT',
                'method2': 'GPT',
                'approach1': 'supervised learning',
                'approach2': 'self-supervised learning',
                'domain': 'natural language processing',
                'task': 'text classification',
                'dataset': 'benchmark datasets',
                'metric': 'accuracy',
                'technique': 'fine-tuning',
                'factor': 'model size',
                'challenge': 'low-resource settings',
                'issue': 'computational efficiency',
                'new_domain': 'medical text',
                'different_task': 'question answering',
                'aspect': 'inference speed',
                'larger_problem': 'large-scale applications',
                'practical_domain': 'healthcare',
                'industry': 'enterprise',
                'application_area': 'document analysis',
                'finding': 'pre-training',
                'field': 'AI applications',
                'variation': 'domain shift',
                'use_case': 'real-time applications',
                'context': 'production environments',
                'phenomenon': 'performance degradation',
                'concept_type': 'embedding',
            }
            
            filled = template
            used_concepts = []
            concept_idx = 0
            
            for placeholder in placeholders:
                if concept_idx < len(concepts):
                    value = concepts[concept_idx]
                    concept_idx += 1
                    used_concepts.append(value)
                else:
                    value = defaults.get(placeholder, 'the approach')
                
                filled = filled.replace('{' + placeholder + '}', value, 1)
            
            return filled
        
        # Use provided concepts
        filled = template
        shuffled_concepts = concepts.copy()
        random.shuffle(shuffled_concepts)
        
        for i, placeholder in enumerate(placeholders):
            if i < len(shuffled_concepts):
                filled = filled.replace('{' + placeholder + '}', shuffled_concepts[i], 1)
        
        return filled
    
    def _extract_used_concepts(self, question: str, concepts: List[str]) -> List[str]:
        """Extract which concepts were used in the question."""
        question_lower = question.lower()
        return [c for c in concepts if c.lower() in question_lower]
    
    def _generate_rationale(self, question_type: QuestionType) -> str:
        """Generate rationale for why this question is relevant."""
        rationales = {
            QuestionType.EXPLORATORY: 
                "Understanding this will provide foundational knowledge for future research.",
            QuestionType.COMPARATIVE: 
                "Comparing approaches helps identify best practices and trade-offs.",
            QuestionType.CAUSAL: 
                "Understanding causality is essential for improving methods.",
            QuestionType.GAP: 
                "Addressing gaps in current research advances the field.",
            QuestionType.EXTENSION: 
                "Extending successful methods to new domains broadens their impact.",
            QuestionType.APPLICATION: 
                "Practical applications demonstrate real-world value.",
            QuestionType.EVALUATION: 
                "Proper evaluation ensures reliable and reproducible results.",
        }
        return rationales.get(question_type, "This question addresses an important research area.")
    
    def _suggest_methods(self, question_type: QuestionType, concepts: List[str]) -> List[str]:
        """Suggest methods to answer the research question."""
        base_methods = {
            QuestionType.EXPLORATORY: [
                "Literature review",
                "Exploratory data analysis",
                "Qualitative analysis",
            ],
            QuestionType.COMPARATIVE: [
                "Controlled experiments",
                "Ablation studies",
                "Statistical significance testing",
            ],
            QuestionType.CAUSAL: [
                "Ablation studies",
                "Intervention experiments",
                "Causal inference methods",
            ],
            QuestionType.GAP: [
                "Novel method development",
                "Hybrid approaches",
                "Transfer learning",
            ],
            QuestionType.EXTENSION: [
                "Domain adaptation",
                "Fine-tuning experiments",
                "Cross-domain evaluation",
            ],
            QuestionType.APPLICATION: [
                "Case studies",
                "User studies",
                "Deployment experiments",
            ],
            QuestionType.EVALUATION: [
                "Benchmark evaluation",
                "Error analysis",
                "Robustness testing",
            ],
        }
        return base_methods.get(question_type, ["Empirical evaluation"])
    
    async def _enhance_with_llm(
        self,
        questions: List[ResearchQuestion],
        concepts: List[str],
    ) -> List[ResearchQuestion]:
        """Use LLM to enhance and refine questions."""
        if not self.llm:
            return questions
        
        try:
            # Create prompt for question enhancement
            prompt = f"""Given these research concepts: {', '.join(concepts[:10])}

Please refine these research questions to be more specific and actionable:

{chr(10).join([f"{i+1}. {q.question}" for i, q in enumerate(questions[:5])])}

For each question, provide:
1. A refined version of the question
2. Why this question is important

Respond in a structured format."""

            response = await self.llm.ainvoke(prompt)
            
            # Parse response and update questions
            # (simplified - in production would parse LLM output)
            return questions
        except Exception:
            return questions
    
    def _score_questions(
        self,
        questions: List[ResearchQuestion],
        concepts: List[str],
    ) -> List[ResearchQuestion]:
        """Score questions by relevance."""
        for q in questions:
            # Base score
            score = 0.5
            
            # Boost for using more concepts
            concept_ratio = len(q.source_concepts) / max(len(concepts), 1)
            score += concept_ratio * 0.3
            
            # Boost for gap and extension questions (often more novel)
            if q.question_type in [QuestionType.GAP, QuestionType.EXTENSION]:
                score += 0.1
            
            # Penalize very short questions
            if len(q.question) < 30:
                score -= 0.1
            
            q.relevance_score = min(max(score, 0.1), 1.0)
        
        return questions
    
    async def generate_followup_questions(
        self,
        query: str,
        context: Optional[str] = None,
        num_questions: int = 5,
    ) -> List[str]:
        """
        Generate follow-up questions based on a query.
        
        Args:
            query: Original query
            context: Optional context (e.g., previous answer)
            num_questions: Number of follow-up questions
            
        Returns:
            List of follow-up question strings
        """
        followup_patterns = [
            "What are the implications of {topic} for {related}?",
            "How does {topic} relate to {related}?",
            "What are the challenges in implementing {topic}?",
            "Can you explain more about {topic}?",
            "What are the alternatives to {topic}?",
            "What evidence supports {topic}?",
            "How has {topic} evolved over time?",
            "What are the limitations of {topic}?",
        ]
        
        # Extract key terms from query
        key_terms = query.split()[:5]
        topic = " ".join(key_terms[:2]) if key_terms else "this topic"
        related = " ".join(key_terms[2:4]) if len(key_terms) > 2 else "related concepts"
        
        followups = []
        for pattern in random.sample(followup_patterns, min(num_questions, len(followup_patterns))):
            question = pattern.format(topic=topic, related=related)
            followups.append(question)
        
        return followups


async def generate_research_questions(
    concepts: List[str],
    num_questions: int = 10,
    llm=None,
    graph_service=None,
) -> List[Dict]:
    """
    Convenience function to generate research questions.
    
    Args:
        concepts: Key concepts to base questions on
        num_questions: Number of questions
        llm: Optional LLM
        graph_service: Optional graph service
        
    Returns:
        List of question dictionaries
    """
    generator = ResearchQuestionGenerator(llm=llm, graph_service=graph_service)
    questions = await generator.generate(concepts=concepts, num_questions=num_questions)
    
    return [
        {
            "question": q.question,
            "type": q.question_type.value,
            "relevance_score": q.relevance_score,
            "source_concepts": q.source_concepts,
            "rationale": q.rationale,
            "suggested_methods": q.suggested_methods,
        }
        for q in questions
    ]
