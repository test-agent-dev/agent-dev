"""
Custom Agent Example - Creating specialized agents
"""
import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.agents.base import BaseAgent, AgentConfig
from src.models.manager import ModelManager


class SQLExpertAgent(BaseAgent):
    """Custom agent specialized in SQL queries and database design"""
    
    def __init__(self, model_manager: ModelManager, model_name: str = "gpt-4"):
        config = AgentConfig(
            name="sql-expert",
            description="Expert in SQL queries, database design, and optimization",
            model_name=model_name,
            instructions="""You are an expert SQL developer and database architect. You help with:

1. Writing and optimizing SQL queries
2. Database schema design and normalization
3. Performance tuning and indexing strategies
4. Data migration and ETL processes
5. SQL best practices and security

Always provide:
- Clear, well-commented SQL code
- Explanations of query logic
- Performance considerations
- Alternative approaches when applicable
- Security recommendations

When writing queries, consider:
- Proper indexing strategies
- Query execution plans
- Data types and constraints
- Normalization principles
- SQL injection prevention""",
            system_prompt="You are a SQL and database expert. Provide clear, optimized, and secure SQL solutions.",
            temperature=0.3,  # Lower temperature for more consistent code
            max_context_length=8000
        )
        super().__init__(config, model_manager)
        
        # Add SQL-specific tools
        self.add_tool("validate_sql", self._validate_sql)
        self.add_tool("explain_query", self._explain_query)
        self.add_tool("optimize_query", self._optimize_query)
    
    async def _validate_sql(self, sql_query: str) -> str:
        """Validate SQL syntax (mock implementation)"""
        # In a real implementation, you'd use sqlparse or similar
        basic_keywords = ['SELECT', 'FROM', 'WHERE', 'JOIN', 'INSERT', 'UPDATE', 'DELETE']
        sql_upper = sql_query.upper()
        
        if any(keyword in sql_upper for keyword in basic_keywords):
            return "✅ SQL syntax appears valid"
        else:
            return "❌ No valid SQL keywords found"
    
    async def _explain_query(self, sql_query: str) -> str:
        """Explain what a query does"""
        # Mock implementation - in reality, you'd parse and analyze
        return f"Query analysis: {sql_query[:100]}..."
    
    async def _optimize_query(self, sql_query: str) -> str:
        """Suggest query optimizations"""
        suggestions = []
        sql_upper = sql_query.upper()
        
        if 'SELECT *' in sql_upper:
            suggestions.append("Consider selecting only needed columns instead of SELECT *")
        
        if 'WHERE' not in sql_upper and 'SELECT' in sql_upper:
            suggestions.append("Consider adding WHERE clause to limit results")
        
        if not suggestions:
            suggestions.append("Query looks well-optimized")
        
        return "Optimization suggestions:\n" + "\n".join(f"- {s}" for s in suggestions)


class CreativeWriterAgent(BaseAgent):
    """Custom agent specialized in creative writing"""
    
    def __init__(self, model_manager: ModelManager, model_name: str = "gpt-4"):
        config = AgentConfig(
            name="creative-writer",
            description="Specialized in creative writing, storytelling, and content creation",
            model_name=model_name,
            instructions="""You are a talented creative writer and storyteller. You excel at:

1. Short stories and flash fiction
2. Poetry and verse
3. Character development
4. Plot construction and narrative arcs
5. Dialogue writing
6. Creative non-fiction
7. Content creation and copywriting

Your writing style is:
- Engaging and immersive
- Rich in descriptive language
- Emotionally resonant
- Well-structured and paced
- Adapted to the requested genre/tone

Always consider:
- Target audience
- Genre conventions
- Tone and mood
- Character voice and consistency
- Show don't tell principle
- Sensory details and imagery""",
            system_prompt="You are a creative writing expert. Craft engaging, well-written content that captivates readers.",
            temperature=0.8,  # Higher temperature for creativity
            max_context_length=8000
        )
        super().__init__(config, model_manager)
        
        # Add writing-specific tools
        self.add_tool("analyze_text", self._analyze_text)
        self.add_tool("suggest_improvements", self._suggest_improvements)
        self.add_tool("generate_prompt", self._generate_prompt)
    
    async def _analyze_text(self, text: str) -> str:
        """Analyze writing style and structure"""
        word_count = len(text.split())
        sentence_count = text.count('.') + text.count('!') + text.count('?')
        avg_sentence_length = word_count / max(sentence_count, 1)
        
        return f"""Text Analysis:
- Word count: {word_count}
- Sentences: {sentence_count}
- Average sentence length: {avg_sentence_length:.1f} words
- Reading level: {'Complex' if avg_sentence_length > 20 else 'Moderate' if avg_sentence_length > 15 else 'Simple'}"""
    
    async def _suggest_improvements(self, text: str) -> str:
        """Suggest writing improvements"""
        suggestions = []
        
        if len(text.split()) < 50:
            suggestions.append("Consider expanding with more descriptive details")
        
        if text.count(',') / len(text.split()) > 0.3:
            suggestions.append("Consider varying sentence structure to reduce comma usage")
        
        if not any(char in text for char in '!?'):
            suggestions.append("Consider adding varied punctuation for emotional impact")
        
        if not suggestions:
            suggestions.append("Writing appears well-structured")
        
        return "Improvement suggestions:\n" + "\n".join(f"- {s}" for s in suggestions)
    
    async def _generate_prompt(self, genre: str, theme: str) -> str:
        """Generate a creative writing prompt"""
        prompts = {
            "fantasy": f"In a world where {theme} determines one's magical abilities...",
            "sci-fi": f"In the year 2157, humanity discovers that {theme} is the key to...",
            "mystery": f"The detective found a clue related to {theme} that changed everything...",
            "romance": f"Two people meet in the most unlikely place, bonded by their shared {theme}...",
            "horror": f"The old house on the hill held a terrible secret about {theme}..."
        }
        
        return prompts.get(genre.lower(), f"Write a story that explores the theme of {theme}...")


class LanguageTutorAgent(BaseAgent):
    """Custom agent for language learning and tutoring"""
    
    def __init__(self, model_manager: ModelManager, target_language: str = "Spanish", model_name: str = "gpt-4"):
        self.target_language = target_language
        
        config = AgentConfig(
            name=f"{target_language.lower()}-tutor",
            description=f"Language tutor specializing in {target_language}",
            model_name=model_name,
            instructions=f"""You are an expert {target_language} language tutor. You help students learn {target_language} through:

1. Grammar explanations and exercises
2. Vocabulary building
3. Pronunciation guidance
4. Conversation practice
5. Cultural context
6. Writing correction
7. Reading comprehension

Your teaching approach:
- Patient and encouraging
- Adaptive to student level
- Provides clear explanations
- Uses examples and context
- Encourages practice
- Corrects mistakes constructively
- Incorporates cultural insights

Always:
- Assess student level appropriately
- Provide pronunciation tips
- Explain grammar rules clearly
- Use real-world examples
- Encourage active practice
- Be patient with mistakes""",
            system_prompt=f"You are a {target_language} language tutor. Be patient, encouraging, and educational.",
            temperature=0.5,
            max_context_length=8000
        )
        super().__init__(config, model_manager)
        
        # Add language-specific tools
        self.add_tool("check_grammar", self._check_grammar)
        self.add_tool("translate_text", self._translate_text)
        self.add_tool("pronunciation_guide", self._pronunciation_guide)
    
    async def _check_grammar(self, text: str) -> str:
        """Check grammar (mock implementation)"""
        # In reality, you'd use language processing libraries
        return f"Grammar check for: '{text}'\n✅ Text appears grammatically correct"
    
    async def _translate_text(self, text: str) -> str:
        """Translate text (mock implementation)"""
        return f"Translation needed for: '{text}'\n(Real translation would be provided here)"
    
    async def _pronunciation_guide(self, word: str) -> str:
        """Provide pronunciation guide"""
        return f"Pronunciation guide for '{word}':\n(Phonetic guide would be provided here)"


async def example_custom_agents():
    """Example of using custom agents"""
    print("🎯 Custom Agents Example")
    
    # Initialize model manager
    model_manager = ModelManager()
    await model_manager.load_models()
    
    # Create custom agents
    sql_agent = SQLExpertAgent(model_manager)
    writer_agent = CreativeWriterAgent(model_manager)
    spanish_tutor = LanguageTutorAgent(model_manager, "Spanish")
    
    # Test SQL agent
    print("\n💾 Testing SQL Expert Agent:")
    sql_response = await sql_agent.process_message(
        "I need help writing a query to find customers who haven't made a purchase in the last 6 months."
    )
    print(f"SQL Expert: {sql_response[:200]}...")
    
    # Test SQL tools
    print("\n🔧 Testing SQL tools:")
    validation = await sql_agent.tools["validate_sql"]("SELECT * FROM customers WHERE last_purchase < NOW() - INTERVAL 6 MONTH")
    print(f"Validation: {validation}")
    
    # Test creative writer
    print("\n✍️ Testing Creative Writer Agent:")
    writer_response = await writer_agent.process_message(
        "Write a short story about a robot who discovers emotions."
    )
    print(f"Writer: {writer_response[:200]}...")
    
    # Test writing tools
    print("\n📝 Testing writing tools:")
    analysis = await writer_agent.tools["analyze_text"]("The robot looked at its reflection and felt something new.")
    print(f"Analysis: {analysis}")
    
    # Test language tutor
    print("\n🗣️ Testing Spanish Tutor Agent:")
    tutor_response = await spanish_tutor.process_message(
        "Can you help me understand the difference between ser and estar?"
    )
    print(f"Spanish Tutor: {tutor_response[:200]}...")
    
    # Test tutor tools
    print("\n🎓 Testing tutor tools:")
    grammar_check = await spanish_tutor.tools["check_grammar"]("Yo soy feliz")
    print(f"Grammar check: {grammar_check}")


if __name__ == "__main__":
    asyncio.run(example_custom_agents())
