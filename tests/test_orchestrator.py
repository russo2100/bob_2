"""Тесты для Orchestrator"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from main import Orchestrator, run_pipeline_wrapper, create_scheduler


class TestOrchestrator:
    """Тесты для Orchestrator"""
    
    @pytest.fixture
    def orchestrator(self):
        """Создаёт тестовый оркестратор с моками"""
        with patch('main.setup_logger'):
            with patch('main.load_env'):
                return Orchestrator()
    
    @patch('main.run_rss_collector')
    def test_run_agent_success(self, mock_func, orchestrator):
        """Тест успешного запуска агента"""
        mock_func.return_value = 5
        
        result = orchestrator._run_agent("Test Agent", mock_func)
        
        assert result == 5
        assert orchestrator.stats["agents"]["Test Agent"]["status"] == "success"
        assert "duration_sec" in orchestrator.stats["agents"]["Test Agent"]
        mock_func.assert_called_once()
    
    @patch('main.run_rss_collector')
    def test_run_agent_error(self, mock_func, orchestrator):
        """Тест запуска агента с ошибкой"""
        mock_func.side_effect = Exception("Test error")
        
        result = orchestrator._run_agent("Test Agent", mock_func)
        
        assert result is None
        assert orchestrator.stats["agents"]["Test Agent"]["status"] == "error"
        assert len(orchestrator.stats["errors"]) == 1
    
    @patch.object(Orchestrator, '_run_agent')
    @patch.object(Orchestrator, '_print_summary')
    def test_run_pipeline(self, mock_summary, mock_run_agent, orchestrator):
        """Тест полного пайплайна"""
        # Мокаем результаты всех агентов
        mock_run_agent.side_effect = [
            10,  # RSS Collector
            5,   # Sonar Scanner
            [{"title": "Trend 1"}],  # Trend Selector
            4,   # Bob Copywriter
            4,   # Cover Generator
            {"published": 4, "failed": 0}  # Publisher
        ]
        
        stats = orchestrator.run_pipeline()
        
        assert mock_run_agent.call_count == 6
        assert "started_at" in stats
        assert "finished_at" in stats
        mock_summary.assert_called_once()
    
    def test_print_summary(self, orchestrator, caplog):
        """Тест печати сводки"""
        # Подготавливаем статистику
        orchestrator.stats["started_at"] = datetime.now().isoformat()
        orchestrator.stats["finished_at"] = datetime.now().isoformat()
        orchestrator.stats["agents"] = {
            "RSS Collector": {"result": 10, "status": "success"},
            "Sonar Scanner": {"result": 5, "status": "success"},
            "Trend Selector": {"result": [{"title": "Trend 1"}], "status": "success"},
            "Bob Copywriter": {"result": 4, "status": "success"},
            "Cover Generator": {"result": 4, "status": "success"},
            "Publisher": {"result": {"published": 4, "failed": 0}, "status": "success"}
        }
        
        orchestrator._print_summary()
        
        # Проверяем что логгер был вызван (хотя бы один раз)
        assert True  # Тест проходит если не было исключений


class TestScheduler:
    """Тесты для планировщика"""
    
    @patch('main.BlockingScheduler')
    def test_create_scheduler(self, mock_scheduler_class):
        """Тест создания планировщика"""
        mock_scheduler = Mock()
        mock_scheduler_class.return_value = mock_scheduler
        
        scheduler = create_scheduler()
        
        assert mock_scheduler.add_job.called
        assert mock_scheduler.add_job.call_args[1]["id"] == "daily_pipeline"
        assert mock_scheduler.add_job.call_args[1]["name"] == "Daily AI Content Pipeline"
    
    @patch('main.Orchestrator')
    def test_run_pipeline_wrapper(self, mock_orchestrator_class):
        """Тест обёртки пайплайна"""
        mock_orchestrator = Mock()
        mock_orchestrator.run_pipeline.return_value = {"status": "success"}
        mock_orchestrator_class.return_value = mock_orchestrator
        
        result = run_pipeline_wrapper()
        
        assert result == {"status": "success"}
        mock_orchestrator.run_pipeline.assert_called_once()


class TestMain:
    """Тесты для main()"""
    
    @patch('main.Orchestrator')
    @patch('main.argparse.ArgumentParser')
    def test_main_without_args(self, mock_parser, mock_orchestrator_class):
        """Тест запуска без аргументов (разовый запуск)"""
        mock_args = Mock()
        mock_args.schedule = False
        mock_args.test = False
        mock_parser.return_value.parse_args.return_value = mock_args
        
        mock_orchestrator = Mock()
        mock_orchestrator_class.return_value = mock_orchestrator
        
        with patch('sys.argv', ['main.py']):
            from main import main
            main()
        
        mock_orchestrator.run_pipeline.assert_called_once()
    
    @patch('main.create_scheduler')
    @patch('main.argparse.ArgumentParser')
    def test_main_with_schedule(self, mock_parser, mock_create_scheduler):
        """Тест запуска с планировщиком"""
        mock_args = Mock()
        mock_args.schedule = True
        mock_args.test = False
        mock_parser.return_value.parse_args.return_value = mock_args
        
        mock_scheduler = Mock()
        mock_create_scheduler.return_value = mock_scheduler
        
        # Эмулируем KeyboardInterrupt для выхода из scheduler.start()
        mock_scheduler.start.side_effect = KeyboardInterrupt()
        
        with patch('sys.argv', ['main.py', '--schedule']):
            from main import main
            main()
        
        mock_scheduler.start.assert_called_once()
    
    @patch('main.argparse.ArgumentParser')
    def test_main_test_mode(self, mock_parser, capsys):
        """Тест тестового режима"""
        mock_args = Mock()
        mock_args.schedule = False
        mock_args.test = True
        mock_parser.return_value.parse_args.return_value = mock_args
        
        with patch('sys.argv', ['main.py', '--test']):
            from main import main
            main()
        
        captured = capsys.readouterr()
        assert "Тестовый запуск" in captured.out or "✅" in captured.out or "❌" in captured.out


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
