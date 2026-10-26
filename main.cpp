#include <iostream>
#include <fstream>
#include <vector>
#include <random>
#include <cmath>
#include <iomanip>
#include <chrono>

struct MarketParameters {
    double initial_price = 100.0;
    double drift = 0.0;           
    double volatility = 0.02;     
    double jump_intensity = 0.05; 
    double jump_mean = 0.0;       
    double jump_volatility = 0.05;
    int time_steps = 1000;
};

struct AgentParameters {
    double gamma = 0.1; 
    double k = 1.5;     
    double A = 1.0;     
    int max_inventory = 15; 
};

struct State {
    int t;
    double mid_price;
    double bid;
    double ask;
    int inventory;
    double cash;
    double total_pnl;
    bool is_shock;
};

class MarketMaker {
private:
    AgentParameters params;
    int inventory = 0;
    double cash = 0.0;

public:
    MarketMaker(AgentParameters p) : params(p) {}

    std::pair<double, double> get_quotes(double mid_price, double market_volatility) {
        double reservation_price = mid_price - (inventory * params.gamma * std::pow(market_volatility, 2));
        double spread = (params.gamma * std::pow(market_volatility, 2)) + 
                        ((2.0 / params.gamma) * std::log(1.0 + (params.gamma / params.k)));

        double bid = reservation_price - (spread / 2.0);
        double ask = reservation_price + (spread / 2.0);

        if (bid >= ask) {
            bid = reservation_price - 0.01;
            ask = reservation_price + 0.01;
        }

        if (inventory >= params.max_inventory) {
            bid = -1e9; 
        } else if (inventory <= -params.max_inventory) {
            ask = 1e9;  
        }

        return {bid, ask};
    }

    void fill_bid(double executed_price) {
        inventory += 1;
        cash -= executed_price;
    }

    void fill_ask(double executed_price) {
        inventory -= 1;
        cash += executed_price;
    }

    int get_inventory() const { return inventory; }
    double get_cash() const { return cash; }
    
    double get_total_pnl(double current_mid_price) const { 
        return cash + (inventory * current_mid_price); 
    }
};

int main(int argc, char* argv[]) {
    std::ios_base::sync_with_stdio(false);

    MarketParameters market_params;
    AgentParameters agent_params;
    
    if (argc >= 4) {
        agent_params.gamma = std::stod(argv[1]);
        agent_params.k = std::stod(argv[2]);
        market_params.jump_intensity = std::stod(argv[3]);
    }

    MarketMaker agent(agent_params);
    std::ios_base::sync_with_stdio(false);

    
    std::random_device rd;
    std::mt19937 gen(rd());
    
    std::normal_distribution<double> standard_normal(0.0, 1.0);
    std::uniform_real_distribution<double> uniform(0.0, 1.0);
    std::normal_distribution<double> jump_normal(market_params.jump_mean, market_params.jump_volatility);

    double current_price = market_params.initial_price;
    double dt = 1.0; 

    std::vector<State> history;
    history.reserve(market_params.time_steps);

    auto start = std::chrono::high_resolution_clock::now();

    for (int t = 1; t <= market_params.time_steps; ++t) {
        double z = standard_normal(gen);
        double gbm_return = (market_params.drift - 0.5 * std::pow(market_params.volatility, 2)) * dt + 
                            market_params.volatility * std::sqrt(dt) * z;
        
        double jump_return = 0.0;
        bool is_shock = false;
        if (uniform(gen) < market_params.jump_intensity) {
            jump_return = jump_normal(gen);
            is_shock = true;
        }

        current_price = current_price * std::exp(gbm_return + jump_return);

        auto [bid, ask] = agent.get_quotes(current_price, market_params.volatility);

        double prob_bid_fill = (bid > 0.0) ? agent_params.A * std::exp(-agent_params.k * (current_price - bid)) : 0.0;
        double prob_ask_fill = (ask < 1e8) ? agent_params.A * std::exp(-agent_params.k * (ask - current_price)) : 0.0;

        if (uniform(gen) < prob_bid_fill) {
            agent.fill_bid(bid);
        }
        if (uniform(gen) < prob_ask_fill) {
            agent.fill_ask(ask);
        }

        history.push_back({t, current_price, bid, ask, agent.get_inventory(), agent.get_cash(), agent.get_total_pnl(current_price), is_shock});
    }

    auto end = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double, std::milli> ms_double = end - start;
    std::cout << "Simulation completed in " << ms_double.count() << " ms\n";

    std::ofstream ledger("simulation_ledger.csv");
    if (!ledger.is_open()) {
        std::cerr << "Failed to open ledger file!\n";
        return 1;
    }
    
    ledger << "TimeStep,MidPrice,AgentBid,AgentAsk,Inventory,Cash,TotalPnL,IsShock\n";
    for (const auto& s : history) {
        ledger << s.t << "," 
               << std::fixed << std::setprecision(4) << s.mid_price << ","
               << s.bid << "," << s.ask << "," 
               << s.inventory << "," 
               << s.cash << ","
               << s.total_pnl << ","
               << (s.is_shock ? 1 : 0) << "\n";
    }

    ledger.close();
    std::cout << "Simulation complete. Data written to simulation_ledger.csv\n";

    return 0;
}